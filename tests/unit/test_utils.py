"""
单元测试 - 通用工具函数
"""
import pytest

from common.utils import get_nested


pytestmark = pytest.mark.unit


class TestGetNested:
    """嵌套取值测试"""

    def test_simple_dot_path(self):
        data = {"data": {"user": {"name": "Alice"}}}
        assert get_nested(data, "data.user.name") == "Alice"

    def test_list_index_bracket(self):
        data = {"data": {"list": [{"id": 1}, {"id": 2}]}}
        assert get_nested(data, "data.list[0].id") == 1
        assert get_nested(data, "data.list[1].id") == 2

    def test_list_index_dot(self):
        data = [{"name": "A"}, {"name": "B"}]
        assert get_nested(data, "0.name") == "A"
        assert get_nested(data, "1.name") == "B"

    def test_mixed_dot_and_bracket(self):
        data = {"data": {"list": [{"tags": ["x", "y"]}]}}
        assert get_nested(data, "data.list[0].tags[1]") == "y"

    def test_missing_key_returns_none(self):
        data = {"a": {"b": 1}}
        assert get_nested(data, "a.c") is None
        assert get_nested(data, "x.y.z") is None

    def test_missing_list_index_returns_none(self):
        data = {"list": [1, 2]}
        assert get_nested(data, "list[5]") is None

    def test_invalid_index_returns_none(self):
        data = {"list": [1, 2]}
        assert get_nested(data, "list[abc]") is None

    def test_non_dict_list_root_returns_none(self):
        assert get_nested("not a dict", "a.b") is None

    def test_empty_path_returns_none(self):
        assert get_nested({"a": 1}, "") is None

    def test_top_level_key(self):
        data = {"id": 42}
        assert get_nested(data, "id") == 42

    def test_none_value_in_path(self):
        data = {"a": None}
        assert get_nested(data, "a.b") is None
