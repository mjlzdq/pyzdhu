"""
UI 自动化场景 1：电商登录流程
使用 https://www.saucedemo.com 作为测试站点
"""
import pytest
from playwright.sync_api import expect
from common.logger import logger


class TestSauceDemoLogin:
    """场景 1: 登录功能 UI 自动化测试"""

    # 测试用户凭据
    USERS = {
        "standard_user": "secret_sauce",
        "locked_out_user": "secret_sauce",
        "problem_user": "secret_sauce",
    }

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_login_success(self, page, base_ui_url):
        """
        TC-UI-001: 正常登录流程
        步骤:
        1. 打开登录页面
        2. 输入用户名和密码
        3. 点击登录按钮
        4. 验证跳转到商品列表页
        """
        logger.info("=" * 50)
        logger.info("UI-场景1: 正常登录流程")
        logger.info("=" * 50)

        # Step 1: 打开登录页
        page.goto(base_ui_url)
        expect(page).to_have_title("Swag Labs")
        logger.info("✓ 登录页面已加载")

        # Step 2: 输入用户名
        username_input = page.locator('[data-test="username"]')
        expect(username_input).to_be_visible()
        username_input.fill("standard_user")
        logger.info("✓ 用户名已输入")

        # Step 3: 输入密码
        password_input = page.locator('[data-test="password"]')
        expect(password_input).to_be_visible()
        password_input.fill("secret_sauce")
        logger.info("✓ 密码已输入")

        # Step 4: 点击登录
        login_btn = page.locator('[data-test="login-button"]')
        expect(login_btn).to_be_enabled()
        login_btn.click()
        logger.info("✓ 登录按钮已点击")

        # Step 5: 验证登录成功 - 检查商品列表页
        products_title = page.locator(".title")
        expect(products_title).to_have_text("Products")
        logger.info("✓ 登录成功，已进入商品列表页")

        # 验证页面元素
        shopping_cart = page.locator(".shopping_cart_link")
        expect(shopping_cart).to_be_visible()
        logger.info("✓ 购物车图标可见")

        # 验证至少有一个商品
        inventory_items = page.locator(".inventory_item")
        item_count = inventory_items.count()
        assert item_count > 0, "商品列表不应为空"
        logger.info(f"✓ 商品列表包含 {item_count} 个商品")

    @pytest.mark.ui
    def test_login_failed_locked_user(self, page, base_ui_url):
        """
        TC-UI-002: 锁定用户登录失败
        验证被锁定的用户无法登录
        """
        logger.info("=" * 50)
        logger.info("UI-场景1: 锁定用户登录")
        logger.info("=" * 50)

        page.goto(base_ui_url)

        # 输入被锁定用户的凭据
        page.locator('[data-test="username"]').fill("locked_out_user")
        page.locator('[data-test="password"]').fill("secret_sauce")
        page.locator('[data-test="login-button"]').click()

        # 验证错误消息
        error_msg = page.locator('[data-test="error"]')
        expect(error_msg).to_be_visible()
        error_text = error_msg.text_content()
        assert "locked out" in error_text.lower(), f"错误消息不匹配: {error_text}"
        logger.info(f"✓ 锁定用户登录失败: {error_text.strip()}")

        # 验证仍在登录页
        expect(page.locator('[data-test="login-button"]')).to_be_visible()
        logger.info("✓ 仍在登录页面")

    @pytest.mark.ui
    def test_login_empty_credentials(self, page, base_ui_url):
        """
        TC-UI-003: 空用户名/密码登录
        验证表单校验
        """
        logger.info("=" * 50)
        logger.info("UI-场景1: 空凭据登录验证")
        logger.info("=" * 50)

        page.goto(base_ui_url)

        # 不输入任何内容直接点击登录
        page.locator('[data-test="login-button"]').click()

        # 验证错误消息
        error_msg = page.locator('[data-test="error"]')
        expect(error_msg).to_be_visible()
        error_text = error_msg.text_content()
        assert "username is required" in error_text.lower()
        logger.info(f"✓ 空用户名验证: {error_text.strip()}")

        # 关闭错误提示
        page.locator('[data-test="error-button"]').click()
        expect(error_msg).not_to_be_visible()
        logger.info("✓ 错误提示已关闭")

    @pytest.mark.ui
    @pytest.mark.parametrize("username,password,expected_error", [
        ("standard_user", "wrong_password", "do not match"),
        ("non_existent_user", "secret_sauce", "do not match"),
    ])
    def test_login_invalid_credentials(self, page, base_ui_url, username, password, expected_error):
        """
        TC-UI-004: 参数化 - 错误凭据登录
        """
        logger.info(f"测试：用户名={username}, 密码={password}")

        page.goto(base_ui_url)
        page.locator('[data-test="username"]').fill(username)
        page.locator('[data-test="password"]').fill(password)
        page.locator('[data-test="login-button"]').click()

        error_msg = page.locator('[data-test="error"]')
        expect(error_msg).to_be_visible()
        error_text = error_msg.text_content()
        assert expected_error in error_text.lower()
        logger.info(f"✓ 验证通过: {error_text.strip()}")
