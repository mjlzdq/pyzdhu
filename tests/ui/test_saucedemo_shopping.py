"""
UI 自动化场景 2：电商购物完整流程
从登录 → 浏览商品 → 添加购物车 → 结算
"""
import pytest
from playwright.sync_api import expect
from common.logger import logger


class TestSauceDemoShopping:
    """场景 2: 完整购物流程 UI 自动化测试"""

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
    def test_add_single_item_to_cart(self, page):
        """
        TC-UI-005: 添加单个商品到购物车
        步骤:
        1. 在商品列表页找到第一个商品
        2. 点击 "Add to cart" 按钮
        3. 验证购物车徽章数字更新
        4. 验证按钮文字变为 "Remove"
        """
        logger.info("=" * 50)
        logger.info("UI-场景2: 添加商品到购物车")
        logger.info("=" * 50)

        # 获取第一个商品的名称
        first_item = page.locator(".inventory_item").first
        item_name = first_item.locator(".inventory_item_name").text_content()
        logger.info(f"商品: {item_name}")

        # 点击添加到购物车
        add_btn = first_item.locator("button")
        expect(add_btn).to_have_text("Add to cart")
        add_btn.click()
        logger.info("✓ 已点击 Add to cart")

        # 验证按钮文字变为 Remove
        expect(add_btn).to_have_text("Remove")
        logger.info("✓ 按钮变为 Remove")

        # 验证购物车徽章
        cart_badge = page.locator(".shopping_cart_badge")
        expect(cart_badge).to_be_visible()
        expect(cart_badge).to_have_text("1")
        logger.info("✓ 购物车徽章显示 1")

    @pytest.mark.ui
    @pytest.mark.smoke
    def test_complete_checkout_flow(self, page):
        """
        TC-UI-006: 完整结算流程
        步骤:
        1. 添加 2 个商品到购物车
        2. 进入购物车页面
        3. 点击 Checkout
        4. 填写收货信息
        5. 点击 Continue
        6. 确认订单总览
        7. 点击 Finish 完成订单
        8. 验证订单成功页面
        """
        logger.info("=" * 50)
        logger.info("UI-场景2: 完整结算流程")
        logger.info("=" * 50)

        # Step 1: 添加 2 个商品
        items = page.locator(".inventory_item")
        for i in range(2):
            item = items.nth(i)
            item_name = item.locator(".inventory_item_name").text_content()
            item.locator("button").click()
            logger.info(f"✓ 已添加: {item_name}")

        # 验证购物车徽章
        cart_badge = page.locator(".shopping_cart_badge")
        expect(cart_badge).to_have_text("2")
        logger.info("✓ 购物车中有 2 个商品")

        # Step 2: 进入购物车
        page.locator(".shopping_cart_link").click()
        expect(page.locator(".title")).to_have_text("Your Cart")
        cart_items = page.locator(".cart_item")
        expect(cart_items).to_have_count(2)
        logger.info("✓ 购物车页面 - 2 个商品")

        # Step 3: 点击 Checkout
        page.locator('[data-test="checkout"]').click()
        expect(page.locator(".title")).to_have_text("Checkout: Your Information")
        logger.info("✓ 进入结算信息页面")

        # Step 4: 填写收货信息
        page.locator('[data-test="firstName"]').fill("张")
        page.locator('[data-test="lastName"]').fill("三")
        page.locator('[data-test="postalCode"]').fill("100000")
        logger.info("✓ 收货信息已填写")

        # Step 5: 点击 Continue
        page.locator('[data-test="continue"]').click()
        expect(page.locator(".title")).to_have_text("Checkout: Overview")
        logger.info("✓ 进入订单总览页面")

        # Step 6: 验证订单信息
        summary_items = page.locator(".cart_item")
        expect(summary_items).to_have_count(2)

        # 验证总金额
        total_label = page.locator(".summary_total_label")
        expect(total_label).to_be_visible()
        total_text = total_label.text_content()
        logger.info(f"订单总金额: {total_text.strip()}")

        # Step 7: 完成订单
        page.locator('[data-test="finish"]').click()

        # Step 8: 验证成功页面
        expect(page.locator(".title")).to_have_text("Checkout: Complete!")
        complete_header = page.locator(".complete-header")
        expect(complete_header).to_have_text("Thank you for your order!")
        logger.info("✓ 订单完成！")

        # 验证返回首页按钮
        back_btn = page.locator('[data-test="back-to-products"]')
        expect(back_btn).to_be_visible()
        logger.info("✓ 返回首页按钮可用")

    @pytest.mark.ui
    def test_remove_item_from_cart(self, page):
        """
        TC-UI-007: 从购物车移除商品
        """
        logger.info("=" * 50)
        logger.info("UI-场景2: 从购物车移除商品")
        logger.info("=" * 50)

        # 添加一个商品
        first_item = page.locator(".inventory_item").first
        item_name = first_item.locator(".inventory_item_name").text_content()
        first_item.locator("button").click()

        # 进入购物车
        page.locator(".shopping_cart_link").click()
        expect(page.locator(".cart_item")).to_have_count(1)
        logger.info(f"✓ 购物车中有: {item_name}")

        # 移除商品
        page.locator('[data-test="remove-sauce-labs-backpack"]').click()
        logger.info("✓ 已点击 Remove")

        # 验证购物车为空
        cart_items = page.locator(".cart_item")
        expect(cart_items).to_have_count(0)
        logger.info("✓ 购物车已清空")

    @pytest.mark.ui
    def test_sort_products(self, page):
        """
        TC-UI-008: 商品排序功能
        """
        logger.info("=" * 50)
        logger.info("UI-场景2: 商品排序")
        logger.info("=" * 50)

        # 获取默认排序下的第一个商品名
        first_default = page.locator(".inventory_item_name").first.text_content()
        logger.info(f"默认排序第一个: {first_default}")

        # 切换排序：价格从低到高
        sort_select = page.locator('[data-test="product-sort-container"]')
        sort_select.select_option("lohi")
        logger.info("✓ 切换为价格从低到高")

        # 获取排序后的价格
        prices = page.locator(".inventory_item_price").all_text_contents()
        numeric_prices = [float(p.replace("$", "")) for p in prices]
        logger.info(f"排序后价格: {numeric_prices}")

        # 验证升序
        assert numeric_prices == sorted(numeric_prices), "价格未按升序排列"
        logger.info("✓ 价格升序排列正确")

        # 切换排序：价格从高到低
        sort_select.select_option("hilo")
        page.wait_for_timeout(500)
        prices_desc = page.locator(".inventory_item_price").all_text_contents()
        numeric_prices_desc = [float(p.replace("$", "")) for p in prices_desc]
        logger.info(f"降序价格: {numeric_prices_desc}")

        assert numeric_prices_desc == sorted(numeric_prices_desc, reverse=True), "价格未按降序排列"
        logger.info("✓ 价格降序排列正确")

    @pytest.mark.ui
    def test_continue_shopping(self, page):
        """
        TC-UI-009: 从购物车返回继续购物
        """
        logger.info("=" * 50)
        logger.info("UI-场景2: 继续购物")
        logger.info("=" * 50)

        # 添加商品并进入购物车
        page.locator(".inventory_item").first.locator("button").click()
        page.locator(".shopping_cart_link").click()

        # 点击继续购物
        page.locator('[data-test="continue-shopping"]').click()

        # 验证返回商品列表页
        expect(page.locator(".title")).to_have_text("Products")
        logger.info("✓ 已返回商品列表页")

        # 购物车徽章应保持
        cart_badge = page.locator(".shopping_cart_badge")
        expect(cart_badge).to_have_text("1")
        logger.info("✓ 购物车仍有 1 个商品")
