"""
UI 测试 conftest - Playwright Fixtures
"""
import pytest
from datetime import datetime
from pathlib import Path
from common.config_loader import config

REPORT_DIR = Path(__file__).parent.parent.parent / "reports" / "screenshots"


def pytest_configure(config):
    """初始化截图目录"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def browser_instance(playwright):
    """
    Session 级别的浏览器实例
    所有 UI 测试共享同一个浏览器进程
    """
    ui_cfg = config.ui_config
    browser_type = ui_cfg.get("browser", "chromium")
    headless = ui_cfg.get("headless", True)

    if browser_type == "firefox":
        browser = playwright.firefox
    elif browser_type == "webkit":
        browser = playwright.webkit
    else:
        browser = playwright.chromium

    browser_instance = browser.launch(
        headless=headless,
        slow_mo=100,
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
    )
    yield browser_instance
    browser_instance.close()


@pytest.fixture(scope="function")
def browser_context(browser_instance):
    """
    Function 级别的浏览器上下文
    每个测试用例独立，避免 localStorage/cookie 残留
    """
    viewport = config.ui_config.get("viewport", {"width": 1920, "height": 1080})
    context = browser_instance.new_context(
        viewport=viewport,
        locale="zh-CN",
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(browser_context):
    """
    每个测试用例独立的 Page 对象
    """
    page = browser_context.new_page()
    page.set_default_timeout(config.ui_config.get("timeout", 30000))
    yield page
    page.close()


@pytest.fixture
def base_ui_url():
    """UI Base URL"""
    return config.ui_base_url


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """失败自动截图"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        if "page" in item.funcargs:
            page = item.funcargs["page"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{item.name}_{timestamp}.png"
            filepath = REPORT_DIR / filename
            try:
                page.screenshot(path=str(filepath), full_page=True)
                print(f"\n📸 失败截图: {filepath}")
            except Exception:
                pass
