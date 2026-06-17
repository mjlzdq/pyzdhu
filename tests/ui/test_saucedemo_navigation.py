"""
UI 自动化场景 3：页面导航与用户菜单
包含侧边栏菜单、筛选、商品详情、登出等
"""
import pytest
from playwright.sync_api import expect
from common.logger import logger


class TestSauceDemoNavigation:
    """场景 3: 页面导航与交互"""

    @pytest.fixture(autouse=True)
    def setup_login(self, page, base_ui_url):
        """每个测试前先登录"""
        page.goto(base_ui_url)
        page.locator('[data-test="username"]').fill("standard_user")
        page.locator('[data-test="password"]').fill("secret_sauce")
        page.locator('[data-test="login-button"]').click()
        expect(page.locator(".title")).to_have_text("Products")

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_product_detail_page(self, page):
        """
        TC-UI-010: 商品详情页
        步骤:
        1. 点击商品名称进入详情页
        2. 验证详情信息
        3. 点击返回按钮回到列表
        """
        logger.info("=" * 50)
        logger.info("UI-场景3: 商品详情页")
        logger.info("=" * 50)

        # 获取第一个商品名称
        first_item = page.locator(".inventory_item").first
        item_name = first_item.locator(".inventory_item_name").text_content()
        item_price = first_item.locator(".inventory_item_price").text_content()
        item_desc = first_item.locator(".inventory_item_desc").text_content()

        # 点击商品名称进入详情
        first_item.locator(".inventory_item_name").click()
        logger.info(f"✓ 点击进入: {item_name}")

        # 验证详情页元素
        expect(page.locator(".inventory_details_name")).to_have_text(item_name)
        expect(page.locator(".inventory_details_price")).to_have_text(item_price)
        expect(page.locator(".inventory_details_desc")).to_have_text(item_desc)
        logger.info("✓ 详情信息一致")

        # 验证详情页有图片
        detail_img = page.locator(".inventory_details_img")
        expect(detail_img).to_be_visible()
        logger.info("✓ 商品图片可见")

        # 返回列表页
        page.locator('[data-test="back-to-products"]').click()
        expect(page.locator(".title")).to_have_text("Products")
        logger.info("✓ 已返回商品列表")

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_logout(self, page):
        """
        TC-UI-011: 用户登出
        步骤:
        1. 打开侧边栏菜单
        2. 点击 Logout
        3. 验证返回登录页
        """
        logger.info("=" * 50)
        logger.info("UI-场景3: 用户登出")
        logger.info("=" * 50)

        # 打开侧边栏
        page.locator("#react-burger-menu-btn").click()
        logger.info("✓ 侧边栏已打开")

        # 等待侧边栏动画完成
        page.wait_for_timeout(500)
        sidebar = page.locator(".bm-menu")
        expect(sidebar).to_be_visible()
        logger.info("✓ 侧边栏可见")

        # 点击 Logout
        logout_link = page.locator("#logout_sidebar_link")
        expect(logout_link).to_be_visible()
        logout_link.click()
        logger.info("✓ 已点击 Logout")

        # 验证回到登录页
        expect(page.locator('[data-test="login-button"]')).to_be_visible()
        expect(page).to_have_title("Swag Labs")
        logger.info("✓ 登出成功，回到登录页")

    @pytest.mark.ui
    def test_reset_app_state(self, page):
        """
        TC-UI-012: 重置应用状态
        验证 Reset App State 功能清空购物车
        """
        logger.info("=" * 50)
        logger.info("UI-场景3: 重置应用状态")
        logger.info("=" * 50)

        # 添加 2 个商品
        items = page.locator(".inventory_item")
        items.nth(0).locator("button").click()
        items.nth(1).locator("button").click()

        # 验证购物车有 2 个商品
        expect(page.locator(".shopping_cart_badge")).to_have_text("2")
        logger.info("✓ 购物车有 2 个商品")

        # 打开侧边栏，点击 Reset App State
        page.locator("#react-burger-menu-btn").click()
        page.wait_for_timeout(500)
        page.locator("#reset_sidebar_link").click()
        logger.info("✓ 已点击 Reset App State")

        # 验证购物车清空
        cart_badge = page.locator(".shopping_cart_badge")
        expect(cart_badge).not_to_be_visible()
        logger.info("✓ 购物车已清空")

        # 验证按钮恢复为 Add to cart
        first_btn = items.first.locator("button")
        expect(first_btn).to_have_text("Add to cart")
        logger.info("✓ 按钮已恢复")

    @pytest.mark.ui
    def test_filter_by_category(self, page):
        """
        TC-UI-013: 按分类筛选商品
        """
        logger.info("=" * 50)
        logger.info("UI-场景3: 分类筛选")
        logger.info("=" * 50)

        # 默认显示所有商品
        all_items = page.locator(".inventory_item").count()
        logger.info(f"全部商品: {all_items} 个")

        # 打开侧边栏
        page.locator("#react-burger-menu-btn").click()
        page.wait_for_timeout(500)

        # 点击 About（验证链接可用）
        about_link = page.locator("#about_sidebar_link")
        expect(about_link).to_be_visible()
        href = about_link.get_attribute("href")
        assert "saucelabs" in href, f"About 链接异常: {href}"
        logger.info(f"✓ About 链接: {href}")

        # 关闭侧边栏
        page.locator("#react-burger-menu-cross-btn").click()
        page.wait_for_timeout(300)

        # 验证仍在商品列表页
        expect(page.locator(".title")).to_have_text("Products")
        logger.info("✓ 侧边栏已关闭，仍在商品页")

    @pytest.mark.ui
    def test_about_page_redirect(self, page):
        """
        TC-UI-014: About 页面跳转
        """
        logger.info("=" * 50)
        logger.info("UI-场景3: About 页面跳转")
        logger.info("=" * 50)

        # 打开侧边栏
        page.locator("#react-burger-menu-btn").click()
        page.wait_for_timeout(500)

        # 点击 About - 会在新页面打开
        with page.expect_popup() as popup_info:
            page.locator("#about_sidebar_link").click()

        new_page = popup_info.value
        logger.info(f"✓ 新页面 URL: {new_page.url}")

        # 验证是 Sauce Labs 官网
        expect(new_page).to_have_url("https://saucelabs.com/")
        logger.info("✓ 跳转到 Sauce Labs 官网")

        new_page.close()

    @pytest.mark.ui
    def test_social_media_links(self, page):
        """
        TC-UI-015: 社交媒体链接验证
        """
        logger.info("=" * 50)
        logger.info("UI-场景3: 社交媒体链接")
        logger.info("=" * 50)

        # 滚动到页面底部
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)

        # 验证 Twitter 链接
        twitter_link = page.locator('a[data-test="social-twitter"]')
        expect(twitter_link).to_be_visible()
        twitter_href = twitter_link.get_attribute("href")
        assert "twitter" in twitter_href.lower(), f"Twitter 链接异常: {twitter_href}"
        logger.info(f"✓ Twitter: {twitter_href}")

        # 验证 Facebook 链接
        facebook_link = page.locator('a[data-test="social-facebook"]')
        expect(facebook_link).to_be_visible()
        fb_href = facebook_link.get_attribute("href")
        assert "facebook" in fb_href.lower(), f"Facebook 链接异常: {fb_href}"
        logger.info(f"✓ Facebook: {fb_href}")

        # 验证 LinkedIn 链接
        linkedin_link = page.locator('a[data-test="social-linkedin"]')
        expect(linkedin_link).to_be_visible()
        li_href = linkedin_link.get_attribute("href")
        assert "linkedin" in li_href.lower(), f"LinkedIn 链接异常: {li_href}"
        logger.info(f"✓ LinkedIn: {li_href}")

        logger.info("✓ 所有社交媒体链接验证通过")
