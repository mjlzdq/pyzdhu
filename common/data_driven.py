"""
数据驱动测试模块 - 断言引擎 & 请求构建器

功能：
- SoftAssertions: 软断言收集器（批量断言，统一报告）
- DDTAssertion: 响应断言引擎（支持嵌套字段、列表验证）
- RequestBuilder: 从数据行构建请求体和查询参数
"""
import json
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from common.logger import logger


class SoftAssertions:
    """
    软断言收集器

    不立即抛出异常，而是收集所有失败，最后统一报告。
    这样一条数据即使有多个断言失败，也能全部反馈出来。
    """

    def __init__(self):
        self._failures: List[str] = []
        self._passed: int = 0
        self._total: int = 0

    def check(self, condition: bool, message: str) -> None:
        """执行一个断言检查，失败时记录"""
        self._total += 1
        if condition:
            self._passed += 1
        else:
            self._failures.append(message)

    def assert_all(self, case_id: str = "") -> None:
        """统一断言：有任何失败则抛出详细异常"""
        if self._failures:
            header = f"\n{'=' * 60}"
            detail = f"\n  [用例 {case_id}] {len(self._failures)}/{self._total} 个断言失败:"
            for i, failure in enumerate(self._failures, 1):
                detail += f"\n    {i}. {failure}"
            footer = f"\n{'=' * 60}"
            raise AssertionError(header + detail + footer)

    @property
    def has_failures(self) -> bool:
        return len(self._failures) > 0

    @property
    def failure_messages(self) -> List[str]:
        return list(self._failures)

    def summary(self) -> str:
        return f"{self._passed}/{self._total} 通过"

    def __bool__(self) -> bool:
        return not self.has_failures


class DDTAssertion:
    """
    DDT 断言引擎

    功能：
    - 对 API 响应做多字段断言
    - 失败时精确反馈是哪个参数不符合预期
    - 支持嵌套字段（如 data.id）
    - 支持特殊字段验证（列表、包含、非空等）
    """

    _SENTINEL = object()

    # 特殊字段关键字
    SPECIAL_FIELDS: set = frozenset({
        "__is_list", "__list_min", "__contains__", "__not_empty",
        "_row_num", "case_id", "description",
    })

    @classmethod
    def assert_response(
        cls,
        response: requests.Response,
        expected_status: int,
        expected_fields: Dict[str, Any],
        case_id: str = "",
        case_desc: str = "",
    ) -> Tuple[bool, str]:
        """
        对 HTTP 响应做完整断言

        Args:
            response: HTTP 响应对象
            expected_status: 期望的状态码
            expected_fields: 期望的响应字段 {字段名: 期望值}
            case_id: 用例编号
            case_desc: 用例描述

        Returns:
            (是否通过, 失败详情字符串)
        """
        sa = SoftAssertions()
        desc = f"[{case_id}] {case_desc}" if case_desc else f"[{case_id}]"

        # 1. 状态码断言
        actual_status = response.status_code
        sa.check(
            actual_status == expected_status,
            f"状态码不匹配: 期望={expected_status}, 实际={actual_status}",
        )

        # 2. 状态码异常时跳过响应体断言
        if actual_status != expected_status:
            logger.warning(f"{desc} 状态码异常 {actual_status} != {expected_status}，跳过响应体断言")
            raise AssertionError(
                f"\n{'=' * 60}\n"
                f"状态码断言失败: 期望 {expected_status}, 实际 {actual_status}\n"
                f"  响应体: {response.text[:500]}\n"
                f"{'=' * 60}"
            )

        # 3. 尝试解析 JSON
        try:
            body = response.json()
        except (json.JSONDecodeError, ValueError):
            sa.check(False, f"响应不是有效 JSON: {response.text[:300]}")
            sa.assert_all(case_id)
            return False, ""

        # 4. 特殊字段检查
        cls._check_special_fields(sa, body, expected_fields)

        # 5. 普通字段断言（支持嵌套路径）
        normal_fields = {k: v for k, v in expected_fields.items()
                         if k not in cls.SPECIAL_FIELDS}
        for field_path, expected_value in normal_fields.items():
            actual_value = cls._get_nested(body, field_path)
            if actual_value is cls._SENTINEL:
                available = list(body.keys()) if isinstance(body, dict) else "N/A"
                sa.check(
                    False,
                    f"字段 [{field_path}] 在响应中不存在\n      可用字段: {available}",
                )
            else:
                sa.check(
                    actual_value == expected_value,
                    f"字段 [{field_path}] 不匹配: 期望={expected_value!r}, 实际={actual_value!r}",
                )

        # 6. 统一报告
        if sa.has_failures:
            logger.error(f"{desc} 断言失败: {sa.summary()}")
        else:
            logger.info(f"{desc} 断言通过: {sa.summary()}")

        sa.assert_all(case_id)
        return True, ""

    @classmethod
    def _check_special_fields(
        cls, sa: SoftAssertions, body: Any, fields: Dict[str, Any]
    ) -> None:
        """检查特殊字段"""
        # __is_list
        if fields.get("__is_list"):
            sa.check(
                isinstance(body, list),
                f"期望响应为列表，实际类型: {type(body).__name__}",
            )

        # __list_min
        if "__list_min" in fields:
            min_count = fields["__list_min"]
            if isinstance(body, list):
                sa.check(
                    len(body) >= min_count,
                    f"列表长度不足: 期望 >= {min_count}, 实际 = {len(body)}",
                )

        # __contains__
        if "__contains__" in fields:
            target = fields["__contains__"]
            if isinstance(body, list):
                found = any(
                    target in str(item)
                    for item in body
                )
                sa.check(found, f"列表中未找到包含 '{target}' 的元素")
            elif isinstance(body, str):
                sa.check(target in body, f"响应字符串中未找到 '{target}'")

        # __not_empty
        if fields.get("__not_empty"):
            if isinstance(body, list):
                sa.check(len(body) > 0, "列表为空")
            elif isinstance(body, dict):
                sa.check(len(body) > 0, "响应对象为空")
            elif isinstance(body, str):
                sa.check(len(body) > 0, "响应字符串为空")

    @classmethod
    def _get_nested(cls, data: Any, path: str) -> Any:
        """获取嵌套字段值，如 "data.user.name" → data["data"]["user"]["name"]"""
        if not path:
            return cls._SENTINEL

        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict):
                if key not in current:
                    return cls._SENTINEL
                current = current[key]
            elif isinstance(current, list):
                try:
                    index = int(key)
                    current = current[index]
                except (ValueError, IndexError):
                    return cls._SENTINEL
            else:
                return cls._SENTINEL

        return current


class RequestBuilder:
    """从数据行构建 HTTP 请求体和查询参数"""

    # 简单模式下自动提取的请求体字段
    SIMPLE_BODY_FIELDS: tuple = (
        "title", "body", "userId", "name", "username",
        "email", "phone", "completed", "id",
    )

    @staticmethod
    def build_expected_fields(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        从数据行中提取期望字段

        提取规则（按优先级）：
        1. expected_response (JSON 字符串或 dict)
        2. expected_fields (JSON 字符串或 dict)
        3. expected_xxx 列（如 expected_title → title）
        """
        fields: Dict[str, Any] = {}

        # 提取 expected_xxx 列（跳过 expected_response/fields 容器）
        skip_keys = {"expected_response", "expected_fields"}
        for key, value in row.items():
            if key.startswith("expected_") and key != "expected_status" and key not in skip_keys:
                field_name = key[len("expected_"):]
                if value != "" and value is not None:
                    fields[field_name] = value

        # 合并 expected_fields（可覆盖 expected_xxx）
        if "expected_fields" in row and row["expected_fields"]:
            ef = RequestBuilder._parse_json_like(row["expected_fields"])
            if isinstance(ef, dict):
                fields.update(ef)

        # 合并 expected_response（最高优先级）
        if "expected_response" in row and row["expected_response"]:
            er = RequestBuilder._parse_json_like(row["expected_response"])
            if isinstance(er, dict):
                fields.update(er)

        return fields

    @staticmethod
    def build_request_body(
        row: Dict[str, Any], format_type: str = "simple"
    ) -> Dict[str, Any]:
        """
        从数据行中构建请求体

        Args:
            row: 数据行
            format_type: "simple"（从列名自动提取）或 "generic"（从 request_body 列解析）
        """
        if format_type == "generic" and "request_body" in row:
            rb = RequestBuilder._parse_json_like(row["request_body"])
            if isinstance(rb, dict):
                return rb
            return {}

        # simple 模式: 从列中自动提取
        body: Dict[str, Any] = {}
        for field in RequestBuilder.SIMPLE_BODY_FIELDS:
            if field in row and row[field] != "" and row[field] is not None:
                body[field] = row[field]
        return body

    @staticmethod
    def build_query_params(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从数据行中构建查询参数（params 列）"""
        if "params" in row and row["params"]:
            p = RequestBuilder._parse_json_like(row["params"])
            if isinstance(p, dict):
                return p
            return {}
        return None

    @staticmethod
    def _parse_json_like(value: Any) -> Any:
        """解析 JSON 字符串或直接返回 dict/list"""
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str) and value.strip():
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return value
        return value
