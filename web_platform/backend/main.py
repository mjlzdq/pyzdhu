"""
接口批量测试平台 - 后端 FastAPI v3.0
功能：CSV/XLSX 批量测试 | 变量提取与链路 | 动态占位符 | 结果导出 Excel | 单接口调试
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from web_platform.backend.routes import run, preview, export, debug

app = FastAPI(title="接口批量测试平台", version="3.0")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

# CORS 安全：默认只允许本地开发环境，生产环境通过环境变量配置白名单
_env = os.environ.get("ENV", "development")
if _env == "production":
    _allow_origins = os.environ.get("CORS_ORIGINS", "").split(",")
    _allow_origins = [o.strip() for o in _allow_origins if o.strip()] or ["http://localhost:8899"]
else:
    _allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def index():
    html_path = FRONTEND_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>前端文件未找到</h1>")


# 注册路由
app.include_router(run.router)
app.include_router(preview.router)
app.include_router(export.router)
app.include_router(debug.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8899)
