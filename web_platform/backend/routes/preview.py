"""
文件预览路由 - /api/preview, /api/preview_full
"""
import json

from fastapi import APIRouter, File, UploadFile

from web_platform.backend.core.parser import parse_file

router = APIRouter()


@router.post("/api/preview")
async def api_preview_file(file: UploadFile = File(...)):
    """预览文件列名和前 3 条内容"""
    filename = file.filename or ""
    content = await file.read()
    rows = parse_file(content, filename)

    safe_preview = []
    for r in rows[:3]:
        safe = {}
        for k, v in r.items():
            safe[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
        safe_preview.append(safe)

    return {
        "total": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "preview": safe_preview,
        "filename": filename,
    }


@router.post("/api/preview_full")
async def api_preview_full(file: UploadFile = File(...)):
    """返回文件全部行数据（用于前端编辑）"""
    content = await file.read()
    rows = parse_file(content, file.filename or "")

    safe_rows = []
    for r in rows:
        safe = {}
        for k, v in r.items():
            safe[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
        safe_rows.append(safe)

    return {
        "total": len(safe_rows),
        "columns": list(safe_rows[0].keys()) if safe_rows else [],
        "rows": safe_rows,
    }
