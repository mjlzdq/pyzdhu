"""
接口测试 - Users（用户）CRUD 操作
"""
import pytest
from common.logger import logger


class TestUsersCRUD:
    """用户 CRUD 接口测试"""

    @pytest.mark.api
    @pytest.mark.smoke
    def test_get_all_users(self, http_client):
        """TC-API-012: 获取所有用户"""
        logger.info("测试：获取所有用户")

        response = http_client.get("/users")

        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 1, "用户列表不应为空"
        logger.info(f"共 {len(users)} 个用户")

    @pytest.mark.api
    def test_get_user_by_id(self, http_client):
        """TC-API-013: 获取单个用户"""
        user_id = 1
        logger.info(f"测试：获取用户 ID={user_id}")

        response = http_client.get(f"/users/{user_id}")

        assert response.status_code == 200
        user = response.json()
        assert user["id"] == user_id
        required_fields = ["name", "username", "email", "address", "phone", "company"]
        for field in required_fields:
            assert field in user, f"缺少字段: {field}"
        logger.info(f"用户: {user['name']} ({user['email']})")

    @pytest.mark.api
    def test_create_user(self, http_client, sample_user_data):
        """TC-API-014: 创建用户"""
        logger.info(f"测试：创建用户 {sample_user_data['name']}")

        response = http_client.post("/users", json=sample_user_data)

        assert response.status_code == 201, f"期望 201, 实际: {response.status_code}"
        data = response.json()
        assert data["name"] == sample_user_data["name"]
        assert data["email"] == sample_user_data["email"]
        assert "id" in data
        logger.info(f"创建成功，ID: {data['id']}")

    @pytest.mark.api
    def test_update_user(self, http_client):
        """TC-API-015: 更新用户信息"""
        user_id = 1
        update_data = {"name": "李四", "email": "lisi@example.com"}
        logger.info(f"测试：更新用户 ID={user_id}")

        response = http_client.put(f"/users/{user_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["email"] == update_data["email"]
        logger.info("更新成功")

    @pytest.mark.api
    def test_delete_user(self, http_client):
        """TC-API-016: 删除用户"""
        user_id = 1
        logger.info(f"测试：删除用户 ID={user_id}")

        response = http_client.delete(f"/users/{user_id}")

        assert response.status_code == 200
        logger.info("删除成功")


class TestUserAlbumsTodos:
    """用户关联数据测试"""

    @pytest.mark.api
    def test_get_user_albums(self, http_client):
        """TC-API-017: 获取用户的相册"""
        user_id = 1
        logger.info(f"测试：获取用户 {user_id} 的相册")

        response = http_client.get(f"/users/{user_id}/albums")

        assert response.status_code == 200
        albums = response.json()
        assert isinstance(albums, list)
        logger.info(f"用户 {user_id} 有 {len(albums)} 个相册")

    @pytest.mark.api
    def test_get_user_todos(self, http_client):
        """TC-API-018: 获取用户的待办事项"""
        user_id = 1
        logger.info(f"测试：获取用户 {user_id} 的待办事项")

        response = http_client.get(f"/users/{user_id}/todos")

        assert response.status_code == 200
        todos = response.json()
        assert isinstance(todos, list)

        # 统计完成情况
        completed = sum(1 for t in todos if t.get("completed"))
        logger.info(
            f"用户 {user_id}: {len(todos)} 个待办, "
            f"已完成 {completed}, 未完成 {len(todos) - completed}"
        )
