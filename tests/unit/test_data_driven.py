"""
单元测试 - DDT 断言引擎与请求构建器

测试：
- SoftAssertions: 软断言收集、统一报告
- DDTAssertion: 响应断言（状态码、字段、嵌套、特殊字段）
- RequestBuilder: 请求体构建、期望字段提取、查询参数
"""
import json
from unittest.mock import MagicMock

import pytest
import requests

from common.data_driven import (
    SoftAssertions, DDTAssertion, RequestBuilder,
)


pytestmark = pytest.mark.unit


# ==================== SoftAssertions ====================

class TestSoftAssertions:
    """软断言收集器测试"""

    def test_all_pass(self):
        sa = SoftAssertions()
        sa.check(True, "should pass 1")
        sa.check(True, "should pass 2")
        sa.assert_all("CASE-01")  # 不应抛出异常
        assert sa.summary() == "2/2 通过"
        assert not sa.has_failures

    def test_some_fail(self):
        sa = SoftAssertions()
        sa.check(True, "pass")
        sa.check(False, "fail 1")
        sa.check(False, "fail 2")

        assert sa.has_failures
        assert sa.summary() == "1/3 通过"

        with pytest.raises(AssertionError) as exc_info:
            sa.assert_all("CASE-02")

        err_msg = str(exc_info.value)
        assert "CASE-02" in err_msg
        assert "2/3 个断言失败" in err_msg
        assert "fail 1" in err_msg
        assert "fail 2" in err_msg

    def test_all_fail(self):
        sa = SoftAssertions()
        sa.check(False, "all bad")
        with pytest.raises(AssertionError):
            sa.assert_all("CASE-03")

    def test_bool_conversion(self):
        """验证 bool() 转换"""
        sa_pass = SoftAssertions()
        sa_pass.check(True, "ok")
        assert bool(sa_pass) is True

        sa_fail = SoftAssertions()
        sa_fail.check(False, "bad")
        assert bool(sa_fail) is False

    def test_failure_messages(self):
        sa = SoftAssertions()
        sa.check(False, "msg1")
        sa.check(False, "msg2")
        msgs = sa.failure_messages
        assert len(msgs) == 2
        assert "msg1" in msgs
        assert "msg2" in msgs


# ==================== DDTAssertion ====================

class TestDDTAssertion:
    """断言引擎测试"""

    @staticmethod
    def _mock_response(status_code: int, body=None) -> MagicMock:
        resp = MagicMock(spec=requests.Response)
        resp.status_code = status_code
        resp.text = json.dumps(body) if body is not None else ""
        resp.json.return_value = body if body is not None else {}
        resp.content = json.dumps(body).encode() if body is not None else b""
        return resp

    def test_status_code_match(self):
        """状态码匹配 - 应通过"""
        resp = self._mock_response(200, {"id": 1})
        passed, _ = DDTAssertion.assert_response(
            resp, expected_status=200, expected_fields={},
            case_id="TC01",
        )
        assert passed is True

    def test_status_code_mismatch_raises(self):
        """状态码不匹配 - 应抛出异常"""
        resp = self._mock_response(404, {})
        with pytest.raises(AssertionError, match="状态码断言失败"):
            DDTAssertion.assert_response(
                resp, expected_status=200, expected_fields={},
                case_id="TC02",
            )

    def test_field_assertion_match(self):
        """字段断言匹配"""
        resp = self._mock_response(201, {"id": 101, "title": "hello"})
        passed, _ = DDTAssertion.assert_response(
            resp, expected_status=201,
            expected_fields={"id": 101, "title": "hello"},
            case_id="TC03",
        )
        assert passed is True

    def test_field_assertion_mismatch(self):
        """字段断言不匹配"""
        resp = self._mock_response(201, {"id": 101, "title": "hello"})
        with pytest.raises(AssertionError, match="断言失败"):
            DDTAssertion.assert_response(
                resp, expected_status=201,
                expected_fields={"title": "wrong"},
                case_id="TC04",
            )

    def test_nested_field(self):
        """嵌套字段断言"""
        resp = self._mock_response(200, {
            "data": {"user": {"name": "Alice", "age": 30}}
        })
        passed, _ = DDTAssertion.assert_response(
            resp, expected_status=200,
            expected_fields={"data.user.name": "Alice", "data.user.age": 30},
            case_id="TC05",
        )
        assert passed is True

    def test_nested_field_not_found(self):
        """嵌套字段不存在"""
        resp = self._mock_response(200, {"data": {"user": {"name": "Alice"}}})
        with pytest.raises(AssertionError, match="不存在"):
            DDTAssertion.assert_response(
                resp, expected_status=200,
                expected_fields={"data.user.age": 30},
                case_id="TC06",
            )

    def test_special_field_is_list(self):
        """特殊字段 __is_list"""
        resp = self._mock_response(200, [{"id": 1}, {"id": 2}])
        passed, _ = DDTAssertion.assert_response(
            resp, expected_status=200,
            expected_fields={"__is_list": True},
            case_id="TC07",
        )
        assert passed is True

    def test_special_field_is_list_fail(self):
        """__is_list 应用于非列表"""
        resp = self._mock_response(200, {"id": 1})
        with pytest.raises(AssertionError, match="期望响应为列表"):
            DDTAssertion.assert_response(
                resp, expected_status=200,
                expected_fields={"__is_list": True},
                case_id="TC08",
            )

    def test_special_field_list_min(self):
        """__list_min 字段"""
        resp = self._mock_response(200, [1, 2, 3, 4, 5])
        passed, _ = DDTAssertion.assert_response(
            resp, expected_status=200,
            expected_fields={"__list_min": 3},
            case_id="TC09",
        )
        assert passed is True

    def test_special_field_list_min_fail(self):
        """__list_min 不足"""
        resp = self._mock_response(200, [1, 2])
        with pytest.raises(AssertionError, match="列表长度不足"):
            DDTAssertion.assert_response(
                resp, expected_status=200,
                expected_fields={"__list_min": 5},
                case_id="TC10",
            )

    def test_special_field_contains(self):
        """__contains__ 字段"""
        resp = self._mock_response(200, ["hello world", "foo bar"])
        passed, _ = DDTAssertion.assert_response(
            resp, expected_status=200,
            expected_fields={"__contains__": "hello"},
            case_id="TC11",
        )
        assert passed is True

    def test_special_field_not_empty(self):
        """__not_empty 字段"""
        resp = self._mock_response(200, [1, 2, 3])
        passed, _ = DDTAssertion.assert_response(
            resp, expected_status=200,
            expected_fields={"__not_empty": True},
            case_id="TC12",
        )
        assert passed is True

    def test_special_field_not_empty_fail(self):
        """__not_empty 应用于空列表"""
        resp = self._mock_response(200, [])
        with pytest.raises(AssertionError, match="列表为空"):
            DDTAssertion.assert_response(
                resp, expected_status=200,
                expected_fields={"__not_empty": True},
                case_id="TC13",
            )

    def test_list_element_access(self):
        """列表索引访问：{field}.0.name"""
        resp = self._mock_response(200, [
            {"name": "Alice"}, {"name": "Bob"},
        ])
        passed, _ = DDTAssertion.assert_response(
            resp, expected_status=200,
            expected_fields={"0.name": "Alice", "1.name": "Bob"},
            case_id="TC14",
        )
        assert passed is True

    def test_non_json_response(self):
        """非 JSON 响应"""
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 200
        resp.text = "plain text, not json"
        resp.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
        resp.content = b"plain text"
        with pytest.raises(AssertionError, match="不是有效 JSON"):
            DDTAssertion.assert_response(
                resp, expected_status=200, expected_fields={},
                case_id="TC15",
            )


# ==================== RequestBuilder ====================

class TestRequestBuilder:
    """请求构建器测试"""

    def test_build_request_body_simple(self):
        """简单模式构建请求体"""
        row = {"title": "test", "body": "content", "userId": 1}
        body = RequestBuilder.build_request_body(row, "simple")
        assert body == {"title": "test", "body": "content", "userId": 1}

    def test_build_request_body_simple_ignore_empty(self):
        """简单模式忽略空值"""
        row = {"title": "test", "body": "", "userId": 1}
        body = RequestBuilder.build_request_body(row, "simple")
        assert body == {"title": "test", "userId": 1}

    def test_build_request_body_generic_json_string(self):
        """通用模式 - JSON 字符串 request_body"""
        row = {"request_body": '{"title":"json body","userId":2}'}
        body = RequestBuilder.build_request_body(row, "generic")
        assert body == {"title": "json body", "userId": 2}

    def test_build_request_body_generic_dict(self):
        """通用模式 - dict request_body（已被 DataReader 解析）"""
        row = {"request_body": {"title": "dict body", "userId": 3}}
        body = RequestBuilder.build_request_body(row, "generic")
        assert body == {"title": "dict body", "userId": 3}

    def test_build_request_body_generic_no_body(self):
        """通用模式 - 无 request_body"""
        row = {"method": "GET"}
        body = RequestBuilder.build_request_body(row, "generic")
        assert body == {}

    def test_build_expected_fields_from_column(self):
        """从 expected_xxx 列提取期望字段"""
        row = {
            "expected_status": 201,
            "expected_title": "hello",
            "expected_userId": 1,
        }
        fields = RequestBuilder.build_expected_fields(row)
        assert fields == {"title": "hello", "userId": 1}

    def test_build_expected_fields_from_json(self):
        """从 expected_response JSON 提取"""
        row = {
            "expected_status": 200,
            "expected_response": '{"id": 1, "name": "test"}',
        }
        fields = RequestBuilder.build_expected_fields(row)
        assert fields == {"id": 1, "name": "test"}

    def test_build_expected_fields_json_override(self):
        """expected_response 覆盖 expected_xxx"""
        row = {
            "expected_status": 200,
            "expected_title": "from column",
            "expected_response": '{"title": "from json"}',
        }
        fields = RequestBuilder.build_expected_fields(row)
        assert fields["title"] == "from json"

    def test_build_expected_fields_ignore_empty(self):
        """忽略空值字段"""
        row = {
            "expected_status": 200,
            "expected_title": "",
            "expected_userId": 1,
        }
        fields = RequestBuilder.build_expected_fields(row)
        assert "title" not in fields
        assert fields["userId"] == 1

    def test_build_query_params(self):
        """构建查询参数"""
        row = {"params": '{"userId": 1, "_limit": 10}'}
        params = RequestBuilder.build_query_params(row)
        assert params == {"userId": 1, "_limit": 10}

    def test_build_query_params_dict(self):
        """查询参数已是 dict"""
        row = {"params": {"key": "value"}}
        params = RequestBuilder.build_query_params(row)
        assert params == {"key": "value"}

    def test_build_query_params_none(self):
        """无查询参数"""
        row = {}
        params = RequestBuilder.build_query_params(row)
        assert params is None

    def test_parse_json_like_string(self):
        """JSON 字符串解析"""
        assert RequestBuilder._parse_json_like('{"a": 1}') == {"a": 1}

    def test_parse_json_like_dict(self):
        """dict 直接返回"""
        assert RequestBuilder._parse_json_like({"a": 1}) == {"a": 1}

    def test_parse_json_like_invalid(self):
        """无效 JSON 返回原字符串"""
        result = RequestBuilder._parse_json_like("not json")
        assert result == "not json"
