"""
数据驱动测试（DDT）— 从 xlsx/csv 文件批量执行

功能：
- 读取 xlsx/csv 测试数据文件
- 逐条发送 API 请求
- 对每个响应的多个字段做断言
- 失败时精确反馈"哪个字段不匹配，期望值 vs 实际值"
- 支持 expect_fail 标记（预期失败用例）

支持两种数据格式：
1. 简单模式：直接定义请求字段（title/body/userId）和期望字段（expected_xxx）
2. 通用模式：定义 method、path、request_body、expected_response
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

from common.data_reader import DataReader
from common.data_driven import DDTAssertion, RequestBuilder, SoftAssertions
from common.logger import logger


# ==================== 常量 ====================

DATA_DIR = Path(__file__).parent.parent.parent / "data"

METHOD_MAP = {
    "GET": "get", "POST": "post", "PUT": "put",
    "PATCH": "patch", "DELETE": "delete", "HEAD": "head",
    "OPTIONS": "options",
}


# ==================== 辅助函数 ====================

def _load_csv_rows(filename: str, exclude_expect_fail: bool = True) -> Tuple[List[Dict], List[str]]:
    """加载 CSV 文件，返回 (rows, ids)，供 parametrize 使用"""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return [], []

    rows = DataReader.read(str(filepath))
    if exclude_expect_fail:
        rows = [
            r for r in rows
            if not str(r.get("expect_fail", "")).lower() in ("true", "yes", "1")
        ]
    ids = [f"{r.get('case_id', '?')}-{r.get('description', '')}" for r in rows]
    return rows, ids


def _execute_row(
    http_client,
    row: Dict[str, Any],
    format_type: str = "simple",
) -> Tuple[str, str]:
    """
    执行单行测试数据：构建请求 → 发送 → 断言响应

    Returns:
        (result_type, message)
        result_type: "passed" | "expected_fail" | "failed"
    """
    case_id = row.get("case_id", "?")
    desc = row.get("description", "")
    row_num = row.get("_row_num", "?")
    expect_fail = str(row.get("expect_fail", "")).lower() in ("true", "yes", "1")

    logger.info(f"\n{'─' * 40}")
    logger.info(f" [{case_id}] {desc} (第{row_num}行)" + (" [预期失败]" if expect_fail else ""))

    # 发送请求
    if format_type == "generic":
        response = _execute_generic_request(http_client, row)
    else:
        response = _execute_simple_request(http_client, row)

    logger.info(f"   响应: {response.status_code}")

    # 断言
    expected_status = int(row.get("expected_status", 200))
    expected_fields = RequestBuilder.build_expected_fields(row)

    try:
        DDTAssertion.assert_response(
            response=response,
            expected_status=expected_status,
            expected_fields=expected_fields,
            case_id=case_id,
            case_desc=desc,
        )
        if expect_fail:
            msg = "⚠️ 意外通过：标记为预期失败但实际通过"
            logger.warning(f"   {msg}")
            return "failed", msg
        return "passed", ""
    except AssertionError as e:
        if expect_fail:
            logger.info(f"   ✓ 预期失败（符合预期）")
            return "expected_fail", str(e)[:300]
        logger.error(f"   ✗ 失败")
        return "failed", str(e)[:500]


def _execute_simple_request(http_client, row: Dict) -> Any:
    """简单模式：POST /posts"""
    body = RequestBuilder.build_request_body(row, "simple")
    logger.info(f"   POST /posts  Body: {json.dumps(body, ensure_ascii=False)[:200]}")
    return http_client.post("/posts", json=body)


def _execute_generic_request(http_client, row: Dict) -> Any:
    """通用模式：根据 method/path 发送请求"""
    method = row.get("method", "GET").upper()
    path = row.get("path", "/")

    kwargs: Dict[str, Any] = {}
    if method in ("POST", "PUT", "PATCH"):
        body = RequestBuilder.build_request_body(row, "generic")
        if body:
            kwargs["json"] = body
            logger.info(f"   {method} {path}  Body: {json.dumps(body, ensure_ascii=False)[:200]}")

    params = RequestBuilder.build_query_params(row)
    if params:
        kwargs["params"] = params

    method_func = getattr(http_client, METHOD_MAP.get(method, "get"), None)
    if method_func is None:
        raise ValueError(f"不支持的 HTTP 方法: {method}")

    return method_func(path, **kwargs)


def _summarize_results(total: int, passed: int, expected_fail: int, failed: List) -> None:
    """打印批量执行结果汇总"""
    logger.info(f"\n{'=' * 60}")
    logger.info(
        f" 批量执行完成: "
        f"总计={total} | 通过={passed} | 预期失败={expected_fail} | 异常失败={len(failed)}"
    )
    logger.info(f"{'=' * 60}")


def _format_failures(failed: List[Dict]) -> str:
    """格式化失败详情"""
    detail = f"\n{'=' * 60}"
    detail += f"\n ❌ 异常失败详情 ({len(failed)} 条)"
    detail += f"\n{'=' * 60}"
    for i, fc in enumerate(failed, 1):
        detail += (
            f"\n  [{fc.get('case_id', '?')}] {fc.get('description', '')}"
            f" (第{fc.get('_row_num', '?')}行)"
        )
        if fc.get("method"):
            detail += f"\n  请求: {fc.get('method', '?')} {fc.get('path', '?')}"
        detail += f"\n  失败原因: {fc.get('error', '未知')[:300]}"
    detail += f"\n{'=' * 60}"
    return detail


# ==================== 简单模式：POST /posts（CSV parametrize）====================

_posts_rows, _posts_ids = _load_csv_rows("sample_posts.csv")


class TestDataDrivenPostsCSV:
    """
    简单模式 — CSV 参数化批量创建文章

    文件格式（sample_posts.csv）：
    ┌──────────┬─────────────┬───────┬──────┬────────┬─────────────────┬────────────────┬─────────────────┬─────────────┐
    │ case_id  │ description │ title │ body │ userId │ expected_status │ expected_title │ expected_userId │ expect_fail │
    └──────────┴─────────────┴───────┴──────┴────────┴─────────────────┴────────────────┴─────────────────┴─────────────┘
    """

    @pytest.mark.ddt
    @pytest.mark.parametrize("test_data", _posts_rows, ids=_posts_ids)
    def test_create_post(self, http_client, test_data):
        """DDT: 从 CSV 读取数据 → POST /posts → 多字段断言"""
        body = RequestBuilder.build_request_body(test_data, "simple")
        response = http_client.post("/posts", json=body)

        expected_status = int(test_data.get("expected_status", 201))
        expected_fields = RequestBuilder.build_expected_fields(test_data)

        DDTAssertion.assert_response(
            response=response,
            expected_status=expected_status,
            expected_fields=expected_fields,
            case_id=test_data.get("case_id", "?"),
            case_desc=test_data.get("description", ""),
        )


# ==================== 简单模式：读取 XLSX ====================

class TestDataDrivenPostsXLSX:
    """简单模式 — XLSX 文件批量执行，单条循环"""

    @pytest.mark.ddt
    def test_create_posts_from_xlsx(self, http_client):
        """DDT: 从 XLSX 读取 → 逐条执行 → 汇总失败详情"""
        filepath = DATA_DIR / "sample_posts.xlsx"
        if not filepath.exists():
            pytest.skip("XLSX 文件不存在，请先运行: python3 generate_sample_data.py")

        rows = DataReader.read_xlsx(str(filepath))
        logger.info(f"\n从 XLSX 读取 {len(rows)} 条数据")

        passed, expected_fail_count = 0, 0
        failed: List[Dict] = []

        for row in rows:
            result, error = _execute_row(http_client, row, "simple")
            if result == "passed":
                passed += 1
            elif result == "expected_fail":
                expected_fail_count += 1
            else:
                failed.append({**row, "error": error})

        _summarize_results(len(rows), passed, expected_fail_count, failed)

        if failed:
            pytest.fail(_format_failures(failed))


# ==================== 通用模式：任意 method/path ====================

class TestDataDrivenGeneric:
    """
    通用模式 — 可定义任意 HTTP 方法和路径

    文件格式（sample_generic.csv）：
    ┌──────────┬─────────────┬────────┬───────────┬──────────────────┬────────┬─────────────────┬─────────────────────────┬─────────────┐
    │ case_id  │ description │ method │ path      │ request_body     │ params │ expected_status │ expected_response (JSON) │ expect_fail │
    └──────────┴─────────────┴────────┴───────────┴──────────────────┴────────┴─────────────────┴─────────────────────────┴─────────────┘
    """

    @pytest.mark.ddt
    def test_generic_from_csv(self, http_client):
        """DDT: 通用模式 — 读取 CSV，逐条执行任意 API 请求"""
        filepath = DATA_DIR / "sample_generic.csv"
        if not filepath.exists():
            pytest.skip(f"数据文件不存在: {filepath}")

        rows = DataReader.read(str(filepath))
        format_type = DataReader.detect_format(rows)
        logger.info(f"\n通用模式: 共 {len(rows)} 条测试数据，格式类型: {format_type}")

        passed, expected_fail_count = 0, 0
        failed: List[Dict] = []

        for row in rows:
            result, error = _execute_row(http_client, row, format_type)
            if result == "passed":
                passed += 1
            elif result == "expected_fail":
                expected_fail_count += 1
            else:
                failed.append({**row, "error": error})

        _summarize_results(len(rows), passed, expected_fail_count, failed)

        if failed:
            pytest.fail(_format_failures(failed))
