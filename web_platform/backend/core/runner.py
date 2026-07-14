"""
批量测试运行器 - 管理变量池、请求构建、响应断言
"""
import json
import time
from typing import Any, Dict, List

from common.http_client import HttpClient, HttpError
from common.utils import get_nested

from web_platform.backend.core.renderer import _render_all_placeholders


def _truncate(data, max_len=2000):
    s = json.dumps(data, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data)
    if len(s) > max_len:
        return s[:max_len] + "...(已截断)"
    return s


class TestRunner:
    """单次批量测试运行器，管理变量池、执行、断言"""

    def __init__(self, base_url: str, cookie: str, timeout: int):
        self.base_url = base_url.rstrip('/')
        self.cookie = cookie
        self.timeout = timeout
        self.pool: Dict[str, Any] = {}

    def run(self, rows: List[Dict]) -> Dict:
        results = []
        status_counts = {"成功": 0, "失败": 0, "异常": 0}
        req_info = {}

        with HttpClient(base_url=self.base_url, timeout=self.timeout) as client:
            if self.cookie:
                client.session.headers["Cookie"] = self.cookie

            for idx, row in enumerate(rows):
                case_id = row.get("case_id", f"行{idx + 1}")
                desc = row.get("description", "")
                start = time.time()
                req_info = {"method": "?", "url": "?"}

                try:
                    row = _render_all_placeholders(row, self.pool)
                    req = self._build_request(row)
                    req_info = {"method": req["method"], "url": req["url"]}
                    headers = req["headers"]

                    response = client.request(
                        req["method"],
                        req["url"],
                        headers=headers,
                        json=req["json"],
                    )
                    elapsed_ms = round((time.time() - start) * 1000)

                    try:
                        resp_body = response.json()
                    except Exception:
                        resp_body = response.text

                    extract_spec = row.get("extract", "")
                    if extract_spec and isinstance(extract_spec, str):
                        self._extract_vars(extract_spec, resp_body)

                    passed, failure_reason = self._assert(
                        row, response, resp_body, elapsed_ms
                    )

                    if passed:
                        status_counts["成功"] += 1
                    else:
                        status_counts["失败"] += 1

                    results.append({
                        "case_id": case_id,
                        "description": desc,
                        "method": req["method"],
                        "url": req["url"],
                        "status_code": response.status_code,
                        "elapsed_ms": elapsed_ms,
                        "passed": passed,
                        "failure_reason": failure_reason,
                        "response_body": _truncate(resp_body),
                        "response_full": (
                            json.dumps(resp_body, ensure_ascii=False)
                            if isinstance(resp_body, (dict, list))
                            else str(resp_body)
                        ),
                    })

                except Exception as e:
                    status_counts["异常"] += 1
                    elapsed = round((time.time() - start) * 1000)
                    results.append({
                        "case_id": case_id,
                        "description": desc,
                        "method": req_info["method"],
                        "url": req_info["url"],
                        "status_code": 0,
                        "elapsed_ms": elapsed,
                        "passed": False,
                        "failure_reason": str(e),
                        "response_body": None,
                        "response_full": str(e),
                    })

        return {
            "total": len(rows),
            "status_counts": status_counts,
            "results": results,
            "variable_pool": self.pool,
            "csv_columns": list(rows[0].keys()) if rows else [],
        }

    def _build_request(self, row: Dict) -> Dict:
        method = row.get("method", "GET").upper()
        path = row.get("path", "/")

        if path.startswith("http"):
            url = path
        elif path.startswith("/"):
            url = self.base_url + path
        else:
            url = self.base_url + "/" + path

        body = None
        if "request_body" in row:
            rb = row["request_body"]
            if isinstance(rb, dict):
                body = rb
            elif isinstance(rb, str) and rb.strip():
                try:
                    body = json.loads(rb)
                except json.JSONDecodeError:
                    body = None

        headers = {"Content-Type": "application/json"}
        if "headers" in row:
            h = row["headers"]
            if isinstance(h, dict):
                headers.update(h)
            elif isinstance(h, str) and h.strip():
                try:
                    headers.update(json.loads(h))
                except json.JSONDecodeError:
                    pass

        return {"method": method, "url": url, "headers": headers, "json": body}

    def _extract_vars(self, spec: str, resp_body: Any):
        """
        提取变量到变量池
        格式: token=data.token | order_id=data.list[0].id
        """
        for pair in spec.split("|"):
            pair = pair.strip()
            if "=" not in pair:
                continue
            name, path = pair.split("=", 1)
            name = name.strip()
            path = path.strip()
            val = get_nested(resp_body, path)
            if val is not None:
                self.pool[name] = val

    def _assert(
        self, row: Dict, response, resp_body: Any, elapsed_ms: int
    ) -> tuple:
        failures = []

        expected_status = row.get("expected_status", "")
        if expected_status:
            try:
                if response.status_code != int(expected_status):
                    failures.append(
                        f"状态码: 期望={expected_status}, 实际={response.status_code}"
                    )
            except ValueError:
                pass

        expected_max_ms = row.get("expected_max_ms", "")
        if expected_max_ms:
            try:
                max_ms = int(expected_max_ms)
                if elapsed_ms > max_ms:
                    failures.append(
                        f"响应超时: 期望≤{max_ms}ms, 实际={elapsed_ms}ms"
                    )
            except ValueError:
                pass

        for key in list(row.keys()):
            if key.startswith("expected_") and key not in (
                "expected_status",
                "expected_max_ms",
            ):
                field_name = key[len("expected_"):]
                expected_val = row[key]
                actual_val = get_nested(resp_body, field_name)

                exp = str(expected_val) if expected_val is not None else ""
                act = str(actual_val) if actual_val is not None else ""
                if exp and exp != act:
                    failures.append(
                        f"[{field_name}] 期望={exp}, 实际={act}"
                    )

        if failures:
            return False, "; ".join(failures)
        return True, ""
