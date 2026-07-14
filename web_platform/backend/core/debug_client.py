"""
单接口调试客户端 - 扩展 HttpClient 记录每次重试尝试
"""
import json
import time
from typing import Any, Dict, Optional

import requests

from common.http_client import HttpClient, HttpError


class _AttemptLogSession(requests.Session):
    """包装 requests.Session，记录每次请求尝试，供 Web 平台展示重试过程。"""

    def __init__(self):
        super().__init__()
        self.attempts: list = []

    def request(self, method, url, **kwargs):
        t0 = time.time()
        try:
            resp = super().request(method, url, **kwargs)
            self.attempts.append({
                "attempt": len(self.attempts) + 1,
                "status_code": resp.status_code,
                "elapsed_ms": round((time.time() - t0) * 1000),
                "retried": False,
                "error": None,
            })
            return resp
        except (requests.Timeout, requests.ConnectionError) as e:
            self.attempts.append({
                "attempt": len(self.attempts) + 1,
                "status_code": 0,
                "elapsed_ms": round((time.time() - t0) * 1000),
                "retried": False,
                "error": f"{type(e).__name__}: {e}",
            })
            raise


class _DebugHttpClient(HttpClient):
    """扩展 HttpClient，使用带尝试日志的 Session。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = _AttemptLogSession()


def _finalize_attempts(attempts: list) -> None:
    """
    回填 retried 标记。
    语义与原始重试逻辑一致：若某次尝试之后还有后续尝试，
    说明它触发了重试（retried=True），最后一次尝试必然为 False。
    """
    last = len(attempts) - 1
    for i, attempt in enumerate(attempts):
        attempt["retried"] = i < last


def _single_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    body: Optional[str] = None,
    timeout: int = 30,
    retry: int = 3,
    retry_delay: float = 1.0,
) -> Dict[str, Any]:
    """
    发送单次 HTTP 请求，带重试机制（复用 common.http_client.HttpClient）。
    返回统一结构，包含请求详情、响应和耗时。
    """
    client = _DebugHttpClient(
        base_url="", timeout=timeout, retry=retry, retry_delay=retry_delay,
    )
    if headers:
        client.session.headers.update(headers)

    req_body_text = body or ""
    json_body = None
    if req_body_text.strip():
        try:
            json_body = json.loads(req_body_text)
        except (json.JSONDecodeError, ValueError):
            pass

    start = time.time()
    try:
        resp = client._request(
            method, url,
            json=json_body,
            data=None if json_body else (req_body_text or None),
        )
    except HttpError as e:
        _finalize_attempts(client.session.attempts)
        return {
            "success": False,
            "request": {
                "method": method.upper(),
                "url": url,
                "headers": dict(client.session.headers),
                "body": req_body_text,
            },
            "error": str(e),
            "attempts": client.session.attempts,
            "retry_used": any(a.get("retried") for a in client.session.attempts),
            "elapsed_ms": round((time.time() - start) * 1000),
        }
    finally:
        client.close()

    _finalize_attempts(client.session.attempts)
    try:
        resp_json = resp.json()
    except Exception:
        resp_json = None

    return {
        "success": True,
        "request": {
            "method": method.upper(),
            "url": url,
            "headers": dict(client.session.headers),
            "body": req_body_text,
        },
        "response": {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body_text": resp.text[:50000],
            "body_json": resp_json,
            "elapsed_ms": round((time.time() - start) * 1000),
            "content_length": len(resp.content),
        },
        "attempts": client.session.attempts,
        "retry_used": any(a.get("retried") for a in client.session.attempts),
    }
