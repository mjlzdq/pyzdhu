"""
单元测试 - ConfigLoader 配置加载器

测试：
- 单例模式正确性
- 多环境切换
- 环境变量覆盖
- get() 方法各场景
- reload() 功能
"""
import os
from unittest.mock import patch

import pytest

from common.config_loader import ConfigLoader, config


class TestConfigLoaderSingleton:
    """单例模式测试"""

    def test_singleton_same_instance(self):
        """验证全局 config 和新建 ConfigLoader 是同一实例"""
        new_loader = ConfigLoader()
        assert new_loader is config

    def test_singleton_after_new(self):
        """多次调用返回同一实例"""
        a = ConfigLoader()
        b = ConfigLoader()
        assert a is b


class TestConfigLoaderProperties:
    """配置属性测试"""

    def test_env_is_test(self):
        """默认环境为 test"""
        assert config.env == "test"

    def test_api_base_url(self):
        """API Base URL 正确加载"""
        assert "jsonplaceholder" in config.api_base_url

    def test_ui_base_url(self):
        """UI Base URL 正确加载"""
        assert "saucedemo" in config.ui_base_url

    def test_api_config_not_empty(self):
        """API 配置不为空"""
        api_cfg = config.api_config
        assert api_cfg["timeout"] == 30
        assert api_cfg["retry"] == 3
        assert "Content-Type" in api_cfg["headers"]

    def test_ui_config_not_empty(self):
        """UI 配置不为空"""
        ui_cfg = config.ui_config
        assert ui_cfg["browser"] == "chromium"
        assert ui_cfg["headless"] is True
        assert ui_cfg["viewport"]["width"] == 1920


class TestConfigLoaderGet:
    """get() 方法测试"""

    def test_get_single_key(self):
        assert config.get("api", "timeout") == 30

    def test_get_nested_key(self):
        assert config.get("ui", "viewport", "width") == 1920

    def test_get_nonexistent_key(self):
        assert config.get("api", "nonexistent") is None

    def test_get_with_default(self):
        assert config.get("api", "nonexistent", default=999) == 999

    def test_get_deep_nonexistent(self):
        assert config.get("a", "b", "c", "d") is None

    def test_get_non_dict_intermediate(self):
        # timeout 是 int，不是 dict，继续向下取会返回 default
        assert config.get("api", "timeout", "nested") is None


class TestConfigLoaderEnvOverride:
    """环境变量覆盖测试"""

    def test_env_override_api_url(self):
        """PYZDHU_API_URL 环境变量应覆盖配置文件"""
        with patch.dict(os.environ, {"PYZDHU_API_URL": "https://override.example.com"}):
            # 需要重新创建实例来应用环境变量
            loader = ConfigLoader()
            # 注意：单例下 config 和 loader 是同一个，api_base_url 使用环境变量
            assert config.api_base_url == "https://override.example.com"

    def test_env_override_env_name(self):
        """PYZDHU_ENV 环境变量应切换环境"""
        with patch.dict(os.environ, {"PYZDHU_ENV": "staging"}):
            assert config.env == "staging"


class TestConfigLoaderReload:
    """reload() 功能测试"""

    def test_reload_does_not_raise(self):
        """reload 不应抛出异常"""
        config.reload()
        assert config.env == "test"
        assert "jsonplaceholder" in config.api_base_url


class TestConfigLoaderEdgeCases:
    """边界情况测试"""

    def test_empty_report_config(self):
        """report 配置存在但可能为空"""
        report = config.report_config
        assert isinstance(report, dict)

    def test_environment_names(self):
        """验证所有环境都有 URL"""
        envs = config._raw_config["environments"]
        for env_name in ["dev", "test", "staging", "prod"]:
            assert env_name in envs
            assert "api_base_url" in envs[env_name]
            assert "ui_base_url" in envs[env_name]
