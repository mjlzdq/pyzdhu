"""
工具模块 - 配置加载器
"""
import os
import yaml
from pathlib import Path


class ConfigLoader:
    """配置加载器，支持多环境配置"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self):
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    @property
    def env(self):
        return self._config.get("environment", "test")

    def get(self, *keys, default=None):
        """通过点号路径获取配置，如 config.get('api', 'timeout')"""
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value

    @property
    def api_base_url(self):
        return self._config["environments"][self.env]["api_base_url"]

    @property
    def ui_base_url(self):
        return self._config["environments"][self.env]["ui_base_url"]

    @property
    def api_config(self):
        return self._config.get("api", {})

    @property
    def ui_config(self):
        return self._config.get("ui", {})


config = ConfigLoader()
