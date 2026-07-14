"""
单接口调试路由 - /api/request
"""
import json
from typing import Optional

from fastapi import APIRouter, Form, HTTPException

from web_platform.backend.core.debug_client import _single_request

router = APIRouter()


@router.post("/api/request")
async def api_send_request(
    method: str = Form("GET"),
    url: str = Form(""),
    headers: str = Form("{}"),
    body: str = Form(""),
    timeout: int = Form(30),
    retry: int = Form(3),
):
    """
    单接口调试 - 发送一次 HTTP 请求并返回完整结果。
    支持方法：GET / POST / PUT / PATCH / DELETE / HEAD / OPTIONS
    重试逻辑与 common/http_client.py 保持一致。
    """
    if not url:
        raise HTTPException(400, "URL 不能为空")

    method = method.upper()
    if method not in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
        raise HTTPException(400, f"不支持的 HTTP 方法: {method}")

    try:
        req_headers = json.loads(headers)
        if not isinstance(req_headers, dict):
            req_headers = {"Content-Type": "application/json"}
    except (json.JSONDecodeError, ValueError):
        req_headers = {"Content-Type": "application/json"}

    timeout = max(1, min(timeout, 300))
    retry = max(0, min(retry, 10))

    result = _single_request(
        method=method,
        url=url,
        headers=req_headers,
        body=body,
        timeout=timeout,
        retry=retry,
    )
    return result
