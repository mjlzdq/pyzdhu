"""
接口测试 - Todos（待办事项）CRUD 操作
"""
import pytest
from common.logger import logger


class TestTodosCRUD:
    """待办事项 CRUD 测试"""

    @pytest.mark.api
    @pytest.mark.smoke
    def test_get_all_todos(self, http_client):
        """TC-API-019: 获取所有待办事项"""
        logger.info("测试：获取所有待办事项")

        response = http_client.get("/todos")

        assert response.status_code == 200
        todos = response.json()
        assert len(todos) > 0, "待办列表不应为空"
        logger.info(f"共 {len(todos)} 个待办事项")

    @pytest.mark.api
    def test_get_todo_by_id(self, http_client):
        """TC-API-020: 获取单个待办事项"""
        todo_id = 1
        logger.info(f"测试：获取待办 ID={todo_id}")

        response = http_client.get(f"/todos/{todo_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert "title" in data
        assert "completed" in data
        logger.info(f"待办: {data['title']}, 完成状态: {data['completed']}")

    @pytest.mark.api
    def test_create_todo(self, http_client):
        """TC-API-021: 创建待办事项"""
        todo_data = {"userId": 1, "title": "编写自动化测试脚本", "completed": False}
        logger.info(f"测试：创建待办 - {todo_data['title']}")

        response = http_client.post("/todos", json=todo_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == todo_data["title"]
        assert data["completed"] == todo_data["completed"]
        assert "id" in data
        logger.info(f"创建成功，ID: {data['id']}")

    @pytest.mark.api
    def test_toggle_todo_completed(self, http_client):
        """TC-API-022: 切换待办完成状态"""
        todo_id = 1
        toggle_data = {"completed": True}
        logger.info(f"测试：切换待办 ID={todo_id} 完成状态")

        response = http_client.patch(f"/todos/{todo_id}", json=toggle_data)

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] == True
        logger.info("状态已切换为完成")

    @pytest.mark.api
    def test_delete_todo(self, http_client):
        """TC-API-023: 删除待办事项"""
        todo_id = 1
        logger.info(f"测试：删除待办 ID={todo_id}")

        response = http_client.delete(f"/todos/{todo_id}")

        assert response.status_code == 200
        logger.info("删除成功")


class TestTodosFiltering:
    """待办事项筛选测试"""

    @pytest.mark.api
    @pytest.mark.parametrize("completed,expected_count", [
        (True, True),
        (False, True),
    ])
    def test_filter_by_completed(self, http_client, completed, expected_count):
        """TC-API-024: 按完成状态筛选"""
        logger.info(f"测试：筛选 completed={completed}")

        response = http_client.get("/todos", params={"completed": str(completed).lower()})

        assert response.status_code == 200
        todos = response.json()
        assert len(todos) > 0 if expected_count else True
        # 验证所有结果的状态一致
        for todo in todos:
            assert todo["completed"] == completed
        logger.info(f"筛选结果: {len(todos)} 条")

    @pytest.mark.api
    def test_filter_by_user(self, http_client):
        """TC-API-025: 按用户筛选"""
        user_id = 1
        logger.info(f"测试：筛选用户 {user_id} 的待办")

        response = http_client.get("/todos", params={"userId": user_id})

        assert response.status_code == 200
        todos = response.json()
        for todo in todos:
            assert todo["userId"] == user_id
        logger.info(f"用户 {user_id} 有 {len(todos)} 个待办")
