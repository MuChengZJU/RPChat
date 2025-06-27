"""
文本处理工具模块
提供文本格式化、清理和处理功能
"""

import re
import html
from typing import List, Optional
from datetime import datetime
from loguru import logger


class TextProcessor:
    """文本处理器"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本，移除多余的空白和特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # HTML解码
        text = html.unescape(text)
        
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        截断文本到指定长度
        
        Args:
            text: 原始文本
            max_length: 最大长度
            suffix: 截断后的后缀
            
        Returns:
            str: 截断后的文本
        """
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        格式化时间戳
        
        Args:
            timestamp: 时间戳
            format_str: 格式字符串
            
        Returns:
            str: 格式化后的时间字符串
        """
        return timestamp.strftime(format_str)
    
    @staticmethod
    def generate_conversation_title(first_message: str, max_length: int = 30) -> str:
        """
        从第一条消息生成对话标题
        
        Args:
            first_message: 第一条消息内容
            max_length: 标题最大长度
            
        Returns:
            str: 生成的标题
        """
        if not first_message:
            return "新对话"
        
        # 清理文本
        title = TextProcessor.clean_text(first_message)
        
        # 移除换行符
        title = title.replace('\n', ' ')
        
        # 截断到合适长度
        title = TextProcessor.truncate_text(title, max_length, "...")
        
        # 如果标题为空，使用默认标题
        if not title.strip():
            title = "新对话"
        
        return title
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 原始文本
            max_keywords: 最大关键词数量
            
        Returns:
            List[str]: 关键词列表
        """
        if not text:
            return []
        
        # 简单的关键词提取：使用长度和频率
        words = re.findall(r'\b\w{2,}\b', text.lower())
        
        # 过滤常见停用词（简化版本）
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'this', 'that', 'is', 'are', 'was', 'were'
        }
        
        # 过滤停用词并统计频率
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序并返回前N个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        return keywords
    
    @staticmethod
    def highlight_keywords(text: str, keywords: List[str]) -> str:
        """
        在文本中高亮关键词
        
        Args:
            text: 原始文本
            keywords: 关键词列表
            
        Returns:
            str: 高亮后的HTML文本
        """
        if not text or not keywords:
            return text
        
        highlighted_text = text
        
        for keyword in keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            highlighted_text = pattern.sub(
                f'<mark>{keyword}</mark>', 
                highlighted_text
            )
        
        return highlighted_text
    
    @staticmethod
    def count_tokens_estimate(text: str) -> int:
        """
        估算文本的token数量（简化版本）
        
        Args:
            text: 文本内容
            
        Returns:
            int: 估算的token数量
        """
        if not text:
            return 0
        
        # 简化的token估算：1个汉字≈1.5tokens，1个英文单词≈1token
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        
        estimated_tokens = int(chinese_chars * 1.5 + english_words)
        
        return estimated_tokens
    
    @staticmethod
    def format_message_for_display(content: str, sender: str, timestamp: datetime) -> str:
        """
        格式化消息用于显示
        
        Args:
            content: 消息内容
            sender: 发送者
            timestamp: 时间戳
            
        Returns:
            str: 格式化的HTML消息
        """
        # 清理和格式化内容
        clean_content = TextProcessor.clean_text(content)
        
        # 处理换行
        formatted_content = clean_content.replace('\n', '<br>')
        
        # 格式化时间
        time_str = TextProcessor.format_timestamp(timestamp, "%H:%M")
        
        # 根据发送者设置样式
        if sender == "用户":
            css_class = "user-message"
            sender_color = "#4CAF50"
        else:
            css_class = "assistant-message"
            sender_color = "#2196F3"
        
        html_message = f"""
        <div class="{css_class}" style="margin: 10px 0;">
            <div style="color: {sender_color}; font-weight: bold; margin-bottom: 5px;">
                {sender} <span style="color: #999; font-size: 0.8em;">{time_str}</span>
            </div>
            <div style="margin-left: 20px;">
                {formatted_content}
            </div>
        </div>
        """
        
        return html_message
    
    @staticmethod
    def search_text(text: str, query: str, case_sensitive: bool = False) -> List[int]:
        """
        在文本中搜索查询字符串的位置
        
        Args:
            text: 要搜索的文本
            query: 查询字符串
            case_sensitive: 是否区分大小写
            
        Returns:
            List[int]: 匹配位置的索引列表
        """
        if not text or not query:
            return []
        
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(re.escape(query), flags)
        
        matches = []
        for match in pattern.finditer(text):
            matches.append(match.start())
        
        return matches 