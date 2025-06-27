"""
OpenAI API客户端模块
负责与LLM服务进行通信，支持OpenAI官方API和兼容的本地服务
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from loguru import logger


@dataclass
class ChatMessage:
    """聊天消息数据类"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[float] = None


@dataclass
class ChatResponse:
    """聊天响应数据类"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class APIClientError(Exception):
    """API客户端异常类"""
    pass


class OpenAIAPIClient:
    """OpenAI API客户端"""
    
    def __init__(self, config_manager):
        """
        初始化API客户端
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        
        # API配置
        self.base_url = self.config.get("api.base_url", "https://api.openai.com/v1")
        self.api_key = self.config.get("api.api_key", "")
        self.model = self.config.get("api.model", "gpt-3.5-turbo")
        self.timeout = self.config.get("api.timeout", 30)
        
        # 请求配置
        self.max_tokens = self.config.get("api.max_tokens", 2000)
        self.temperature = self.config.get("api.temperature", 0.7)
        
        logger.info(f"初始化API客户端: {self.base_url}, 模型: {self.model}")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "RPChat/1.0.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _build_chat_payload(self, messages: List[ChatMessage], stream: bool = False) -> Dict[str, Any]:
        """
        构建聊天请求载荷
        
        Args:
            messages: 消息列表
            stream: 是否使用流式响应
            
        Returns:
            Dict[str, Any]: 请求载荷
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": msg.role, "content": msg.content} 
                for msg in messages
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": stream
        }
        
        return payload
    
    async def chat_completion(self, messages: List[ChatMessage]) -> ChatResponse:
        """
        发送聊天完成请求
        
        Args:
            messages: 消息历史列表
            
        Returns:
            ChatResponse: 聊天响应
            
        Raises:
            APIClientError: API请求失败
        """
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = self._get_headers()
        payload = self._build_chat_payload(messages)
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.debug(f"发送API请求: {url}")
                logger.trace(f"请求载荷: {json.dumps(payload, ensure_ascii=False, indent=2)}")
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API请求失败: {response.status} - {error_text}")
                        raise APIClientError(f"API请求失败: {response.status} - {error_text}")
                    
                    response_data = await response.json()
                    logger.trace(f"API响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    
                    return self._parse_chat_response(response_data)
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP请求错误: {e}")
            raise APIClientError(f"HTTP请求错误: {e}")
        except Exception as e:
            logger.error(f"API请求异常: {e}")
            raise APIClientError(f"API请求异常: {e}")
    
    async def chat_completion_stream(self, messages: List[ChatMessage]) -> AsyncGenerator[str, None]:
        """
        发送流式聊天完成请求
        
        Args:
            messages: 消息历史列表
            
        Yields:
            str: 流式响应的文本片段
            
        Raises:
            APIClientError: API请求失败
        """
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = self._get_headers()
        payload = self._build_chat_payload(messages, stream=True)
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.debug(f"发送流式API请求: {url}")
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"流式API请求失败: {response.status} - {error_text}")
                        raise APIClientError(f"流式API请求失败: {response.status} - {error_text}")
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if line.startswith('data: '):
                            data = line[6:]  # 移除 'data: ' 前缀
                            
                            if data == '[DONE]':
                                break
                            
                            try:
                                chunk_data = json.loads(data)
                                
                                if 'choices' in chunk_data and chunk_data['choices']:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    
                                    if content:
                                        yield content
                                        
                            except json.JSONDecodeError:
                                continue  # 跳过无效的JSON行
                
        except aiohttp.ClientError as e:
            logger.error(f"流式HTTP请求错误: {e}")
            raise APIClientError(f"流式HTTP请求错误: {e}")
        except Exception as e:
            logger.error(f"流式API请求异常: {e}")
            raise APIClientError(f"流式API请求异常: {e}")
    
    def _parse_chat_response(self, response_data: Dict[str, Any]) -> ChatResponse:
        """
        解析聊天响应数据
        
        Args:
            response_data: API响应数据
            
        Returns:
            ChatResponse: 解析后的响应对象
        """
        try:
            choice = response_data['choices'][0]
            message = choice['message']
            
            return ChatResponse(
                content=message['content'],
                model=response_data['model'],
                usage=response_data.get('usage', {}),
                finish_reason=choice.get('finish_reason', 'unknown')
            )
            
        except (KeyError, IndexError) as e:
            logger.error(f"解析API响应失败: {e}")
            logger.debug(f"响应数据: {response_data}")
            raise APIClientError(f"解析API响应失败: {e}")
    
    async def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            bool: 连接成功返回True
        """
        try:
            test_messages = [
                ChatMessage(role="user", content="Hello, this is a connection test.")
            ]
            
            await self.chat_completion(test_messages)
            logger.info("API连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            return False
    
    def update_config(self, config_manager):
        """
        更新配置
        
        Args:
            config_manager: 新的配置管理器
        """
        self.config = config_manager
        
        # 更新API配置
        self.base_url = self.config.get("api.base_url", "https://api.openai.com/v1")
        self.api_key = self.config.get("api.api_key", "")
        self.model = self.config.get("api.model", "gpt-3.5-turbo")
        self.timeout = self.config.get("api.timeout", 30)
        self.max_tokens = self.config.get("api.max_tokens", 2000)
        self.temperature = self.config.get("api.temperature", 0.7)
        
        logger.info("API客户端配置已更新")
    
    @property
    def is_local_api(self) -> bool:
        """判断是否为本地API服务"""
        return 'localhost' in self.base_url or '127.0.0.1' in self.base_url or '192.168.' in self.base_url
        
    def cleanup(self):
        """清理API客户端资源"""
        logger.info("API客户端资源已清理") 