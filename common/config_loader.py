"""
配置加载器模块 - 支持多环境配置与环境变量覆盖
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigLoader:
    """配置加载器（线程安全单例），支持多环境配置和环境变量覆盖"""

    _instance: Optional["ConfigLoader"] = None

    def __new__(cls) -> "ConfigLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = None
        return cls._instance

    def _load_config(self) -> None:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    @property
    def _raw_config(self) -> Dict[str, Any]:
        if self._config is None:
            self._load_config()
        return self._config

    @property
    def env(self) -> str:
        """当前环境名称（可通过 PYZDHU_ENV 环境变量覆盖）"""
        return os.environ.get("PYZDHU_ENV", self._raw_config.get("environment", "test"))

    def get(self, *keys: str, default: Any = None) -> Any:
        """通过点号路径获取配置，如 config.get('api', 'timeout')"""
        value = self._raw_config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value

    @property
    def api_base_url(self) -> str:
        """API Base URL（可通过 PYZDHU_API_URL 环境变量覆盖）"""
        return os.environ.get(
            "PYZDHU_API_URL",
            self._raw_config["environments"][self.env]["api_base_url"],
        )

    @property
    def ui_base_url(self) -> str:
        """UI Base URL（可通过 PYZDHU_UI_URL 环境变量覆盖）"""
        return os.environ.get(
            "PYZDHU_UI_URL",
            self._raw_config["environments"][self.env]["ui_base_url"],
        )

    @property
    def api_config(self) -> Dict[str, Any]:
        return self._raw_config.get("api", {})

    @property
    def ui_config(self) -> Dict[str, Any]:
        return self._raw_config.get("ui", {})

    @property
    def report_config(self) -> Dict[str, Any]:
        return self._raw_config.get("report", {})

    def reload(self) -> None:
        """强制重新加载配置文件（主要用于测试）"""
        self._config = None
        self._load_config()


# 全局单例实例
config = ConfigLoader()
