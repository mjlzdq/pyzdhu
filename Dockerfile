# 接口批量测试平台 - 统一镜像（同时支持 Web 服务 与 容器内 pytest）
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 系统级依赖：Playwright 浏览器运行所需的基础库
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制整个项目（含 common / tests / data / web_platform）
COPY . /app

# 安装依赖：
#  - requirements.txt：pytest / playwright / openpyxl 等测试依赖
#  - fastapi + uvicorn：Web 服务依赖（根 requirements 未包含）
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install "fastapi>=0.110.0" "uvicorn>=0.27.0" "python-multipart>=0.0.6"

# 安装 Playwright 浏览器（运行 -m ui 标记测试所需）。
# 若只跑 unit/api/ddt 等无需浏览器的用例，可注释掉本行以显著加快构建。
RUN playwright install --with-deps chromium

# Web 服务端口
EXPOSE 8899

# 默认启动 Web 服务：从项目根运行，确保 PROJECT_ROOT / FRONTEND_DIR 路径正确。
# 在容器内跑 pytest 时直接覆盖命令即可，例如：
#   docker run --rm pyzdhu pytest
#   docker run --rm pyzdhu pytest -m "unit or api" -v
#   docker run --rm pyzdhu pytest tests/api/test_data_driven.py -v
CMD ["python", "web_platform/backend/main.py"]
