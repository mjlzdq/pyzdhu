"""
接口测试 - Posts（文章）CRUD 操作
使用 jsonplaceholder 作为测试 API
"""
import pytest
from common.logger import logger


class TestPostsCRUD:
    """文章 CRUD 接口测试"""

    # ==================== 查询（Read）====================

    @pytest.mark.api
    @pytest.mark.smoke
    def test_get_all_posts(self, http_client):
        """TC-API-001: 获取所有文章列表"""
        logger.info("测试：获取所有文章")
        response = http_client.get("/posts")

        assert response.status_code == 200, f"状态码异常: {response.status_code}"
        posts = response.json()
        assert isinstance(posts, list), "响应应该是列表"
        assert len(posts) > 0, "文章列表不应为空"
        # 验证结构
        assert "userId" in posts[0], "缺少 userId 字段"
        assert "id" in posts[0], "缺少 id 字段"
        assert "title" in posts[0], "缺少 title 字段"
        assert "body" in posts[0], "缺少 body 字段"
        logger.info(f"获取到 {len(posts)} 篇文章")

    @pytest.mark.api
    def test_get_post_by_id(self, http_client):
        """TC-API-002: 根据 ID 获取单篇文章"""
        post_id = 1
        logger.info(f"测试：获取文章 ID={post_id}")

        response = http_client.get(f"/posts/{post_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == post_id, "返回的文章 ID 不匹配"
        assert data["userId"] == 1
        assert data["title"], "title 不应为空"
        assert data["body"], "body 不应为空"
        logger.info(f"文章标题: {data['title']}")

    @pytest.mark.api
    def test_get_post_not_found(self, http_client):
        """TC-API-003: 获取不存在的文章应返回 404"""
        logger.info("测试：获取不存在的文章")
        response = http_client.get("/posts/99999")
        assert response.status_code == 404, f"期望 404, 实际: {response.status_code}"

    # ==================== 创建（Create）====================

    @pytest.mark.api
    @pytest.mark.smoke
    def test_create_post(self, http_client, sample_post_data):
        """TC-API-004: 创建新文章"""
        logger.info(f"测试：创建文章 - {sample_post_data['title']}")

        response = http_client.post("/posts", json=sample_post_data)

        assert response.status_code == 201, f"期望 201, 实际: {response.status_code}"
        data = response.json()
        assert data["title"] == sample_post_data["title"]
        assert data["body"] == sample_post_data["body"]
        assert data["userId"] == sample_post_data["userId"]
        assert "id" in data, "创建后应返回 id"
        logger.info(f"创建成功，ID: {data['id']}")

    @pytest.mark.api
    @pytest.mark.parametrize("field,invalid_value", [
        ("title", ""),
        ("body", ""),
        ("userId", None),
    ])
    def test_create_post_validation(self, http_client, sample_post_data, field, invalid_value):
        """TC-API-005: 参数化 - 创建文章必填字段验证"""
        logger.info(f"测试：创建文章 - {field}={invalid_value}")
        data = {**sample_post_data, field: invalid_value}
        response = http_client.post("/posts", json=data)
        # jsonplaceholder 为模拟 API，对无效数据仍返回 201，
        # 此处仅验证请求可被正常接收和处理
        assert response.status_code in [200, 201], f"意外状态码: {response.status_code}"

    # ==================== 更新（Update）====================

    @pytest.mark.api
    def test_update_post_full(self, http_client):
        """TC-API-006: 全量更新文章（PUT）"""
        post_id = 1
        update_data = {
            "id": post_id,
            "title": "更新后的标题",
            "body": "更新后的内容",
            "userId": 1,
        }
        logger.info(f"测试：全量更新文章 ID={post_id}")

        response = http_client.put(f"/posts/{post_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["body"] == update_data["body"]
        logger.info(f"更新成功: {data['title']}")

    @pytest.mark.api
    def test_update_post_partial(self, http_client):
        """TC-API-007: 部分更新文章（PATCH）"""
        post_id = 1
        patch_data = {"title": "PATCH 更新标题"}
        logger.info(f"测试：部分更新文章 ID={post_id}")

        response = http_client.patch(f"/posts/{post_id}", json=patch_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == patch_data["title"]
        logger.info(f"PATCH 成功: {data['title']}")

    # ==================== 删除（Delete）====================

    @pytest.mark.api
    def test_delete_post(self, http_client):
        """TC-API-008: 删除文章"""
        post_id = 1
        logger.info(f"测试：删除文章 ID={post_id}")

        response = http_client.delete(f"/posts/{post_id}")

        assert response.status_code == 200, f"期望 200, 实际: {response.status_code}"
        logger.info("删除成功")


class TestPostsFiltering:
    """文章查询过滤测试"""

    @pytest.mark.api
    def test_filter_posts_by_user(self, http_client):
        """TC-API-009: 按用户 ID 筛选文章"""
        user_id = 1
        logger.info(f"测试：查询用户 {user_id} 的文章")

        response = http_client.get(f"/posts", params={"userId": user_id})

        assert response.status_code == 200
        posts = response.json()
        assert len(posts) > 0, "该用户应有文章"
        # 所有文章都应属于该用户
        for post in posts:
            assert post["userId"] == user_id, f"文章 {post['id']} 不属于用户 {user_id}"
        logger.info(f"用户 {user_id} 共有 {len(posts)} 篇文章")

    @pytest.mark.api
    def test_pagination(self, http_client):
        """TC-API-010: 分页查询"""
        logger.info("测试：分页查询文章")

        page_size = 10
        response = http_client.get("/posts", params={"_page": 1, "_limit": page_size})

        assert response.status_code == 200
        posts = response.json()
        assert len(posts) <= page_size, f"超出分页限制: {len(posts)} > {page_size}"
        logger.info(f"分页结果: {len(posts)} 条")


class TestPostsComments:
    """文章评论关联测试"""

    @pytest.mark.api
    def test_get_post_comments(self, http_client):
        """TC-API-011: 获取文章的评论"""
        post_id = 1
        logger.info(f"测试：获取文章 {post_id} 的评论")

        response = http_client.get(f"/posts/{post_id}/comments")

        assert response.status_code == 200
        comments = response.json()
        assert isinstance(comments, list)
        if comments:
            assert "email" in comments[0]
            assert "body" in comments[0]
        logger.info(f"文章 {post_id} 有 {len(comments)} 条评论")
