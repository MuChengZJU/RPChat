"""
本地存储管理模块
负责对话历史的持久化存储和会话管理
"""

import asyncio
import aiosqlite
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from loguru import logger

from core.api_client import ChatMessage


@dataclass
class Conversation:
    """对话会话数据类"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    model: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': self.message_count,
            'model': self.model
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """从字典创建对象"""
        return cls(
            id=data['id'],
            title=data['title'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            message_count=data.get('message_count', 0),
            model=data.get('model', '')
        )


@dataclass  
class StoredMessage:
    """存储的消息数据类"""
    id: int
    conversation_id: str
    role: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoredMessage':
        """从字典创建对象"""
        return cls(
            id=data['id'],
            conversation_id=data['conversation_id'],
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


class StorageManager:
    """存储管理器"""
    
    def __init__(self, config_manager):
        """
        初始化存储管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.db_path = Path(self.config.get("storage.database_path", "data/rpchat.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_connection = None
        self._initialized = False
        
        logger.info(f"初始化存储管理器: {self.db_path}")
    
    async def initialize(self):
        """初始化数据库"""
        if self._initialized:
            return
        
        try:
            self.db_connection = await aiosqlite.connect(str(self.db_path))
            await self._create_tables()
            self._initialized = True
            logger.info("数据库初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def _create_tables(self):
        """创建数据库表"""
        # 创建对话表
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                model TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}'
            )
        """)
        
        # 创建消息表
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    ON DELETE CASCADE
            )
        """)
        
        # 创建索引
        await self.db_connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
            ON messages (conversation_id)
        """)
        
        await self.db_connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
            ON messages (timestamp)
        """)
        
        await self.db_connection.commit()
        logger.debug("数据库表创建完成")
    
    async def create_conversation(self, title: str, model: str = "") -> Conversation:
        """
        创建新对话
        
        Args:
            title: 对话标题
            model: 使用的模型名称
            
        Returns:
            Conversation: 创建的对话对象
        """
        if not self._initialized:
            await self.initialize()
        
        now = datetime.now(timezone.utc)
        conversation_id = f"conv_{int(now.timestamp() * 1000000)}"
        
        conversation = Conversation(
            id=conversation_id,
            title=title,
            created_at=now,
            updated_at=now,
            model=model
        )
        
        await self.db_connection.execute("""
            INSERT INTO conversations (id, title, created_at, updated_at, model)
            VALUES (?, ?, ?, ?, ?)
        """, (
            conversation.id,
            conversation.title,
            conversation.created_at.isoformat(),
            conversation.updated_at.isoformat(),
            conversation.model
        ))
        
        await self.db_connection.commit()
        logger.info(f"创建新对话: {conversation.id} - {title}")
        
        return conversation
    
    async def get_conversations(self, limit: int = 100) -> List[Conversation]:
        """
        获取对话列表
        
        Args:
            limit: 限制返回数量
            
        Returns:
            List[Conversation]: 对话列表
        """
        if not self._initialized:
            await self.initialize()
        
        cursor = await self.db_connection.execute("""
            SELECT id, title, created_at, updated_at, message_count, model
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = await cursor.fetchall()
        conversations = []
        
        for row in rows:
            conversation = Conversation(
                id=row[0],
                title=row[1],
                created_at=datetime.fromisoformat(row[2]),
                updated_at=datetime.fromisoformat(row[3]),
                message_count=row[4],
                model=row[5]
            )
            conversations.append(conversation)
        
        logger.debug(f"获取到 {len(conversations)} 个对话")
        return conversations
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        获取指定对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            Optional[Conversation]: 对话对象或None
        """
        if not self._initialized:
            await self.initialize()
        
        cursor = await self.db_connection.execute("""
            SELECT id, title, created_at, updated_at, message_count, model
            FROM conversations
            WHERE id = ?
        """, (conversation_id,))
        
        row = await cursor.fetchone()
        if row:
            return Conversation(
                id=row[0],
                title=row[1],
                created_at=datetime.fromisoformat(row[2]),
                updated_at=datetime.fromisoformat(row[3]),
                message_count=row[4],
                model=row[5]
            )
        
        return None
    
    async def update_conversation(self, conversation: Conversation):
        """
        更新对话信息
        
        Args:
            conversation: 对话对象
        """
        if not self._initialized:
            await self.initialize()
        
        conversation.updated_at = datetime.now(timezone.utc)
        
        await self.db_connection.execute("""
            UPDATE conversations 
            SET title = ?, updated_at = ?, message_count = ?, model = ?
            WHERE id = ?
        """, (
            conversation.title,
            conversation.updated_at.isoformat(),
            conversation.message_count,
            conversation.model,
            conversation.id
        ))
        
        await self.db_connection.commit()
        logger.debug(f"更新对话: {conversation.id}")
    
    async def delete_conversation(self, conversation_id: str):
        """
        删除对话及其所有消息
        
        Args:
            conversation_id: 对话ID
        """
        if not self._initialized:
            await self.initialize()
        
        await self.db_connection.execute("""
            DELETE FROM conversations WHERE id = ?
        """, (conversation_id,))
        
        await self.db_connection.commit()
        logger.info(f"删除对话: {conversation_id}")
    
    async def add_message(self, conversation_id: str, message: ChatMessage) -> StoredMessage:
        """
        添加消息到对话
        
        Args:
            conversation_id: 对话ID
            message: 聊天消息
            
        Returns:
            StoredMessage: 存储的消息对象
        """
        if not self._initialized:
            await self.initialize()
        
        timestamp = datetime.now(timezone.utc)
        
        cursor = await self.db_connection.execute("""
            INSERT INTO messages (conversation_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            conversation_id,
            message.role,
            message.content,
            timestamp.isoformat()
        ))
        
        message_id = cursor.lastrowid
        
        # 更新对话的消息计数
        await self.db_connection.execute("""
            UPDATE conversations 
            SET message_count = message_count + 1, updated_at = ?
            WHERE id = ?
        """, (timestamp.isoformat(), conversation_id))
        
        await self.db_connection.commit()
        
        stored_message = StoredMessage(
            id=message_id,
            conversation_id=conversation_id,
            role=message.role,
            content=message.content,
            timestamp=timestamp
        )
        
        logger.debug(f"添加消息到对话 {conversation_id}: {message.role}")
        return stored_message
    
    async def get_messages(self, conversation_id: str, limit: int = 100) -> List[StoredMessage]:
        """
        获取对话的消息列表
        
        Args:
            conversation_id: 对话ID
            limit: 限制返回数量
            
        Returns:
            List[StoredMessage]: 消息列表
        """
        if not self._initialized:
            await self.initialize()
        
        cursor = await self.db_connection.execute("""
            SELECT id, conversation_id, role, content, timestamp, metadata
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (conversation_id, limit))
        
        rows = await cursor.fetchall()
        messages = []
        
        for row in rows:
            metadata = json.loads(row[5]) if row[5] else {}
            message = StoredMessage(
                id=row[0],
                conversation_id=row[1],
                role=row[2],
                content=row[3],
                timestamp=datetime.fromisoformat(row[4]),
                metadata=metadata
            )
            messages.append(message)
        
        logger.debug(f"获取对话 {conversation_id} 的 {len(messages)} 条消息")
        return messages
    
    async def search_conversations(self, query: str, limit: int = 20) -> List[Conversation]:
        """
        搜索对话
        
        Args:
            query: 搜索关键词
            limit: 限制返回数量
            
        Returns:
            List[Conversation]: 匹配的对话列表
        """
        if not self._initialized:
            await self.initialize()
        
        cursor = await self.db_connection.execute("""
            SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at, c.message_count, c.model
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.title LIKE ? OR m.content LIKE ?
            ORDER BY c.updated_at DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        rows = await cursor.fetchall()
        conversations = []
        
        for row in rows:
            conversation = Conversation(
                id=row[0],
                title=row[1],
                created_at=datetime.fromisoformat(row[2]),
                updated_at=datetime.fromisoformat(row[3]),
                message_count=row[4],
                model=row[5]
            )
            conversations.append(conversation)
        
        logger.debug(f"搜索到 {len(conversations)} 个匹配的对话")
        return conversations
    
    async def export_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        导出对话数据
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            Dict[str, Any]: 导出的对话数据
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"对话不存在: {conversation_id}")
        
        messages = await self.get_messages(conversation_id)
        
        export_data = {
            'conversation': conversation.to_dict(),
            'messages': [msg.to_dict() for msg in messages],
            'export_timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0'
        }
        
        logger.info(f"导出对话: {conversation_id}")
        return export_data
    
    async def import_conversation(self, data: Dict[str, Any]) -> Conversation:
        """
        导入对话数据
        
        Args:
            data: 导入的对话数据
            
        Returns:
            Conversation: 导入的对话对象
        """
        conv_data = data['conversation']
        messages_data = data['messages']
        
        # 创建新的对话ID避免冲突
        now = datetime.now(timezone.utc)
        new_conversation_id = f"conv_{int(now.timestamp() * 1000000)}"
        
        conversation = Conversation(
            id=new_conversation_id,
            title=f"[导入] {conv_data['title']}",
            created_at=now,
            updated_at=now,
            model=conv_data.get('model', '')
        )
        
        await self.db_connection.execute("""
            INSERT INTO conversations (id, title, created_at, updated_at, model)
            VALUES (?, ?, ?, ?, ?)
        """, (
            conversation.id,
            conversation.title,
            conversation.created_at.isoformat(),
            conversation.updated_at.isoformat(),
            conversation.model
        ))
        
        # 导入消息
        for msg_data in messages_data:
            message = ChatMessage(
                role=msg_data['role'],
                content=msg_data['content']
            )
            await self.add_message(conversation.id, message)
        
        await self.db_connection.commit()
        logger.info(f"导入对话完成: {conversation.id}")
        
        return conversation
    
    async def cleanup(self):
        """清理资源"""
        if self.db_connection:
            await self.db_connection.close()
            self.db_connection = None
            self._initialized = False
            logger.info("存储管理器资源已清理") 