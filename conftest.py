"""
conftest.py - Pytest 全局配置与 Fixtures

提供：
- 全局 HTTP 客户端 fixtures
- 通用测试数据 fixtures
- Allure 报告增强（环境信息、失败截图）
- 自定义标记注册
"""
import os
from datetime import datetime
from pathlib import Path

import allure
import pytest

from common.http_client import HttpClient
from common.config_loader import config


# ==================== HTTP 客户端 Fixtures ====================

@pytest.fixture(scope="session")
def http_client():
    """Session 级别的 HTTP 客户端（共享连接池）"""
    with HttpClient() as client:
        yield client


@pytest.fixture(scope="function")
def api_client():
    """Function 级别的 HTTP 客户端（每个用例独立）"""
    with HttpClient() as client:
        yield client


# ==================== URL Fixtures ====================

@pytest.fixture
def api_base_url() -> str:
    """API Base URL"""
    return config.api_base_url


# ==================== 测试数据 Fixtures ====================

@pytest.fixture
def sample_post_data() -> dict:
    """创建文章的示例数据"""
    return {
        "title": "测试文章标题",
        "body": "这是测试文章的内容",
        "userId": 1,
    }


@pytest.fixture
def sample_user_data() -> dict:
    """创建用户的示例数据"""
    return {
        "name": "张三",
        "username": "zhangsan",
        "email": "zhangsan@example.com",
        "phone": "13800138000",
    }


@pytest.fixture
def sample_todo_data() -> dict:
    """创建待办的示例数据"""
    return {
        "userId": 1,
        "title": "编写自动化测试脚本",
        "completed": False,
    }


# ==================== 工具 Fixtures ====================

@pytest.fixture
def project_root() -> Path:
    """项目根目录"""
    return Path(__file__).parent


@pytest.fixture
def data_dir(project_root: Path) -> Path:
    """测试数据目录"""
    return project_root / "data"


@pytest.fixture
def report_dir(project_root: Path) -> Path:
    """报告目录"""
    return project_root / "reports"


# ==================== Pytest 钩子 ====================

def pytest_configure(config):
    """注册自定义标记"""
    markers = [
        ("smoke", "冒烟测试用例"),
        ("regression", "回归测试用例"),
        ("api", "接口测试用例"),
        ("ui", "UI 测试用例"),
        ("ddt", "数据驱动测试用例"),
        ("slow", "慢速测试用例"),
        ("unit", "单元测试用例"),
    ]
    for name, desc in markers:
        config.addinivalue_line("markers", f"{name}: {desc}")


def pytest_sessionstart(session):
    """会话开始时写入 Allure 环境信息"""
    allure_dir = session.config.option.allure_report_dir
    if allure_dir:
        os.makedirs(allure_dir, exist_ok=True)
        env_file = os.path.join(allure_dir, "environment.properties")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"Environment={config.env.upper()}\n")
            f.write(f"API.BaseURL={config.api_base_url}\n")
            f.write(f"UI.BaseURL={config.ui_base_url}\n")
            f.write(f"Browser={config.ui_config.get('browser', 'chromium')}\n")
            f.write(f"Headless={config.ui_config.get('headless', True)}\n")
            import sys
            f.write(f"Python={sys.version.split()[0]}\n")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """失败时自动截图并附加堆栈到 Allure 报告"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # Playwright 失败截图
        page = item.funcargs.get("page")
        if page:
            _attach_failure_screenshot(item, page)

        # 附加异常堆栈
        if call.excinfo:
            allure.attach(
                str(call.excinfo),
                name="异常堆栈",
                attachment_type=allure.attachment_type.TEXT,
            )


def _attach_failure_screenshot(item, page) -> None:
    """失败时截图并附加到 Allure"""
    try:
        screenshot_dir = Path(__file__).parent / "reports" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{item.name}_{timestamp}.png"
        filepath = screenshot_dir / filename
        page.screenshot(path=str(filepath), full_page=True)

        allure.attach.file(
            str(filepath),
            name=f"失败截图 - {item.name}",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """测试环境信息输出"""
    print(f"\n{'=' * 50}")
    print(f" 测试环境: {config.env.upper()}")
    print(f" API 地址: {config.api_base_url}")
    print(f" UI  地址: {config.ui_base_url}")
    print(f"{'=' * 50}\n")
    yield
    print(f"\n{'=' * 50}")
    print(f" 测试完成")
    print(f"{'=' * 50}\n")
