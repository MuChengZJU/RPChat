"""
配置管理器模块
负责加载、保存和管理应用程序配置
"""

import os
import toml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为项目根目录下的config
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = config_dir
            
        self.config_file = self.config_dir / "config.toml"
        self.template_file = self.config_dir / "config.template.toml"
        
        self._config: Dict[str, Any] = {}
        self._default_config: Dict[str, Any] = {}
        
        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)
        
    def load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            # 首先加载默认配置模板
            self._load_default_config()
            
            # 如果配置文件不存在，创建默认配置文件
            if not self.config_file.exists():
                logger.warning(f"配置文件不存在: {self.config_file}")
                self._create_default_config()
            
            # 加载用户配置
            with open(self.config_file, 'r', encoding='utf-8') as f:
                user_config = toml.load(f)
            
            # 合并默认配置和用户配置
            self._config = self._merge_configs(self._default_config, user_config)
            
            logger.info(f"配置文件加载成功: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            # 使用默认配置作为fallback
            self._config = self._default_config.copy()
            return False
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                toml.dump(self._config, f)
            
            logger.info(f"配置文件保存成功: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持嵌套键（用.分隔）
        
        Args:
            key: 配置键，支持嵌套格式如 "api.model"
            default: 默认值
            
        Returns:
            Any: 配置值或默认值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.warning(f"配置键不存在: {key}，使用默认值: {default}")
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值，支持嵌套键
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 创建嵌套字典结构
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.debug(f"设置配置: {key} = {value}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置段
        
        Args:
            section: 配置段名称
            
        Returns:
            Dict[str, Any]: 配置段内容
        """
        return self._config.get(section, {})
    
    def _load_default_config(self) -> None:
        """加载默认配置模板"""
        try:
            if self.template_file.exists():
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    self._default_config = toml.load(f)
                logger.debug("默认配置模板加载成功")
            else:
                logger.warning("默认配置模板文件不存在")
                self._default_config = self._get_fallback_config()
        except Exception as e:
            logger.error(f"加载默认配置模板失败: {e}")
            self._default_config = self._get_fallback_config()
    
    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        try:
            if self.template_file.exists():
                # 复制模板文件
                import shutil
                shutil.copy2(self.template_file, self.config_file)
                logger.info(f"已创建默认配置文件: {self.config_file}")
            else:
                # 创建基本配置文件
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    toml.dump(self._default_config, f)
                logger.info(f"已创建基本配置文件: {self.config_file}")
                
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并默认配置和用户配置
        
        Args:
            default: 默认配置
            user: 用户配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """获取fallback配置"""
        return {
            "application": {
                "name": "RPChat",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "api": {
                "base_url": "https://api.openai.com/v1",
                "api_key": "",
                "model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.7,
                "timeout": 30
            },
            "ui": {
                "theme": "dark",
                "font_family": "Microsoft YaHei",
                "font_size": 12,
                "window_width": 1000,
                "window_height": 700
            }
        }
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        return self._config.copy()
    
    def validate_config(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            bool: 配置有效返回True
        """
        try:
            # 验证必需的配置项
            required_sections = ['application', 'api', 'ui']
            for section in required_sections:
                if section not in self._config:
                    logger.error(f"缺少必需的配置段: {section}")
                    return False
            
            # 验证API配置
            api_config = self._config.get('api', {})
            if not api_config.get('base_url'):
                logger.error("API base_url 配置为空")
                return False
            
            logger.info("配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False 