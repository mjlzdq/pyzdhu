"""
批量测试路由 - /api/run
"""
import json
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from web_platform.backend.core.parser import parse_file
from web_platform.backend.core.runner import TestRunner

router = APIRouter()


@router.post("/api/run")
async def api_run_tests(
    file: Optional[UploadFile] = File(None),
    baseUrl: str = Form(""),
    cookie: str = Form(""),
    timeout: int = Form(30),
    rows_json: str = Form(""),
    init_vars_json: str = Form(""),
):
    """
    批量执行接口测试
    支持 CSV / XLSX 上传 或 手动添加用例（rows_json），自动渲染占位符、提取变量、执行断言
    """
    if rows_json:
        rows = json.loads(rows_json)
    elif file and file.filename:
        content = await file.read()
        rows = parse_file(content, file.filename or "")
    else:
        raise HTTPException(400, "请上传文件或手动添加用例")

    if not rows:
        raise HTTPException(400, "文件为空或格式不正确")

    runner = TestRunner(baseUrl, cookie, timeout)

    if init_vars_json:
        try:
            init_vars = json.loads(init_vars_json)
            if isinstance(init_vars, dict):
                runner.pool.update(init_vars)
        except json.JSONDecodeError:
            pass

    result = runner.run(rows)
    return result
