"""
配置管理器：管理数据库连接和数据源配置
"""

import configparser
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置目录路径，默认为项目根目录下的config目录
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(exist_ok=True)

        # 默认配置文件路径
        self.default_config_file = self.config_dir / "database.ini"
        self.data_sources_file = self.config_dir / "data_sources.json"

        # 加载数据源配置
        self._load_data_sources()

    def _load_data_sources(self):
        """加载数据源配置"""
        if self.data_sources_file.exists():
            try:
                with open(self.data_sources_file, "r", encoding="utf-8") as f:
                    self.data_sources = json.load(f)
            except Exception as e:
                logger.warning(f"加载数据源配置失败: {e}")
                self.data_sources = {}
        else:
            self.data_sources = {}

    def get_default_database_config(self) -> Dict[str, Any]:
        """
        获取默认数据库配置

        Returns:
            数据库配置字典
        """
        if not self.default_config_file.exists():
            raise FileNotFoundError(
                f"默认配置文件不存在: {self.default_config_file}\n"
                "请创建配置文件或使用database_config参数"
            )

        config = configparser.ConfigParser()
        try:
            with open(self.default_config_file, "r", encoding="utf-8") as f:
                config.read_file(f)
        except UnicodeDecodeError:
            with open(self.default_config_file, "r", encoding="gbk") as f:
                config.read_file(f)

        if "postgresql" not in config:
            raise ValueError("配置文件中缺少[postgresql]节")

        db_config = config["postgresql"]
        return {
            "host": db_config.get("host", "localhost"),
            "port": db_config.getint("port", 5432),
            "database": db_config.get("database"),
            "user": db_config.get("user"),
            "password": db_config.get("password"),
        }

    def get_data_source(self, source_name: str) -> Dict[str, Any]:
        """
        获取指定数据源配置

        Args:
            source_name: 数据源名称

        Returns:
            数据源配置字典
        """
        if source_name not in self.data_sources:
            raise ValueError(f"数据源 '{source_name}' 不存在")

        return self.data_sources[source_name]

    def list_data_sources(self) -> List[str]:
        """
        列出所有已配置的数据源

        Returns:
            数据源名称列表
        """
        return list(self.data_sources.keys())

    def register_data_source(self, source_name: str, config: Dict[str, Any]):
        """
        注册新的数据源

        Args:
            source_name: 数据源名称
            config: 数据源配置
        """
        self.data_sources[source_name] = config
        self._save_data_sources()

    def _save_data_sources(self):
        """保存数据源配置"""
        try:
            with open(self.data_sources_file, "w", encoding="utf-8") as f:
                json.dump(self.data_sources, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据源配置失败: {e}")
