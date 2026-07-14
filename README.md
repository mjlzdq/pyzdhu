# Pyzdhu - Python 自动化测试框架

基于 **Pytest + Requests + Playwright** 的 Python 自动化测试框架，支持接口测试和 UI 测试，内置 HTML + Allure 双报告。

## 目录

- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [运行测试](#运行测试)
- [查看报告](#查看报告)
- [手动调试](#手动调试)
- [测试用例概览](#测试用例概览)
- [配置说明](#配置说明)
- [自定义标记](#自定义标记)
- [核心特性](#核心特性)
- [常见问题](#常见问题)

## 项目结构

```
pyzdhu/
├── common/                          # 公共模块
│   ├── __init__.py
│   ├── config_loader.py             # 多环境配置加载器
│   ├── http_client.py               # HTTP 客户端（自动重试 + Session 管理）
│   ├── logger.py                    # 统一日志工具
│   ├── data_reader.py               # xlsx/csv 数据文件读取器
│   └── data_driven.py               # DDT 断言引擎 + 失败参数反馈
├── config/
│   └── config.yaml                  # 主配置文件（环境 / 超时 / 浏览器 等）
├── data/                            # 测试数据文件
│   ├── sample_posts.csv             #   简单模式示例
│   ├── sample_posts.xlsx            #   XLSX 示例
│   └── sample_generic.csv           #   通用模式示例
├── tests/
│   ├── __init__.py
│   ├── unit/                        # 单元测试（框架自身测试）
│   │   ├── __init__.py
│   │   ├── test_config_loader.py    #   配置加载器测试（18 条）
│   │   ├── test_http_client.py      #   HTTP 客户端测试（21 条）
│   │   ├── test_data_reader.py      #   数据读取器测试（16 条）
│   │   ├── test_data_driven.py      #   断言引擎测试（46 条）
│   │   └── test_logger.py           #   日志模块测试（7 条）
│   ├── api/                         # 接口自动化测试
│   │   ├── __init__.py
│   │   ├── test_posts.py            #   文章 CRUD、筛选、评论（11 条）
│   │   ├── test_users.py            #   用户 CRUD、相册、待办（7 条）
│   │   ├── test_todos.py            #   待办 CRUD、筛选（7 条）
│   │   └── test_data_driven.py      #   数据驱动测试（xlsx/csv 批量执行）
│   └── ui/                          # UI 自动化测试
│       ├── __init__.py
│       ├── conftest.py              #   Playwright fixtures + 失败截图
│       ├── test_saucedemo_login.py      #   场景一：登录流程
│       ├── test_saucedemo_shopping.py   #   场景二：购物流程
│       └── test_saucedemo_navigation.py #   场景三：页面导航交互
├── reports/
│   ├── html/                        # HTML 报告输出
│   ├── allure-results/              # Allure 原始结果数据
│   ├── allure-report/               # Allure 静态报告
│   └── screenshots/                 # 失败截图
├── conftest.py                      # 全局 Fixtures + Allure 环境信息钩子
├── generate_allure.py               # 纯 Python Allure 报告生成器（零额外依赖）
├── generate_sample_data.py          # 测试数据生成器（CSV → XLSX）
├── pytest.ini                       # Pytest 配置（标记、日志、默认参数）
├── requirements.txt                 # Python 依赖清单
├── run_tests.sh                     # 一键运行脚本
└── README.md
```

## 快速开始

### 1. 克隆并安装依赖

```bash
cd pyzdhu

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright Chromium 浏览器（UI 测试需要）
playwright install chromium
```

或一键安装：

```bash
./run_tests.sh install
```

### 2. 环境要求

| 组件 | 最低版本 |
|------|----------|
| Python | 3.9+ |
| pip | 21.0+ |
| Node.js | 16+（Playwright 依赖，macOS 通常已内置） |

## 运行测试

### 通过脚本运行（推荐）

```bash
./run_tests.sh api      # 接口测试（25 条）
./run_tests.sh ui       # UI 测试（15 条）
./run_tests.sh smoke    # 冒烟测试
./run_tests.sh all      # 全部测试
./run_tests.sh clean    # 清理测试报告
```

### 通过 pytest 命令运行

```bash
# 按标记运行
pytest tests/api/ -v -m api
pytest tests/ui/ -v -m ui
pytest tests/ -v -m smoke

# 单个文件
pytest tests/api/test_posts.py -v

# 单个类
pytest tests/api/test_posts.py::TestPostsCRUD -v

# 单个用例
pytest tests/api/test_posts.py::TestPostsCRUD::test_get_all_posts -v

# UI 测试 - 非无头模式（可看到浏览器操作过程）
pytest tests/ui/ -v -m ui --headed

# UI 测试 - 慢速模式（每步延迟，方便观察）
pytest tests/ui/ -v -m ui --headed --slowmo=1000

# 并行执行（自动利用多核）
pytest tests/api/ -v -n auto
```

### 数据驱动测试（DDT）

> 从 CSV / XLSX 文件读取测试数据，逐条发送请求并断言，失败时精确反馈哪个参数不匹配。

```bash
# 运行数据驱动测试
pytest tests/api/test_data_driven.py -v -m ddt

# 只跑 CSV 参数化模式
pytest tests/api/test_data_driven.py::TestDataDrivenPostsCSV -v

# 只跑通用模式（任意 method/path）
pytest tests/api/test_data_driven.py::TestDataDrivenGeneric -v
```

**数据文件格式**（`data/sample_posts.csv`）：

| case_id | description | title | body | userId | expected_status | expected_title | expected_userId | expect_fail |
|---------|-------------|-------|------|--------|-----------------|----------------|-----------------|-------------|
| DDT-001 | 正常创建文章 | 测试标题 | 内容 | 1 | 201 | 测试标题 | 1 | |
| DDT-005 | 验证失败反馈 | 错误标题 | 内容 | 1 | 201 | 不匹配标题 | 1 | true |

**失败反馈示例**：

```
字段 [title] 不匹配: 期望='不匹配标题', 实际='错误标题'
```

**通用模式**（`data/sample_generic.csv`）支持任意 HTTP 方法和路径：

| case_id | description | method | path | request_body | expected_response (JSON) |
|---------|-------------|--------|------|-------------|--------------------------|
| DDT-G01 | 获取文章列表 | GET | /posts | | {"__is_list":true,"__list_min":50} |
| DDT-G04 | 创建文章 | POST | /posts | {"title":"测试"} | {"title":"测试"} |

**期望字段特殊标记**：

| 标记 | 说明 |
|------|------|
| `__is_list` | 验证响应是列表 |
| `__list_min` | 列表最小长度 |
| `__not_empty` | 验证响应非空 |
| `__contains__` | 列表中包含指定值 |

## 查看报告

### HTML 报告

```bash
# 通过脚本打开
./run_tests.sh html api_report
./run_tests.sh html ui_report
./run_tests.sh html smoke_report
./run_tests.sh html full_report

# 或直接打开文件
open reports/html/api_report.html
```

### Allure 报告

> 纯 Python 实现，无需安装 Homebrew / allure 命令行工具。

```bash
# 一键生成并打开
./run_tests.sh allure

# 或手动两步
python3 generate_allure.py
open reports/allure-report/index.html
```

Allure 报告包含：汇总卡片、通过率进度条、环境信息、按功能分组的用例列表、失败原因。

## 手动调试

不通过 pytest 命令行，直接在 IDE 中运行和调试：

- **右键运行**：打开任意 `test_*.py` 文件，IDE 左侧会显示 ▶ 运行按钮，点击即可运行单个用例
- **断点调试**：在测试函数内打断点，右键选择 Debug 即可步进调试
- **`-s` 参数**：`pytest tests/api/test_posts.py -v -s` 可在终端看到 `print()` 输出
- **`--lf` 参数**：`pytest tests/api/ --lf` 只重跑上次失败的用例
- **`-x` 参数**：`pytest tests/api/ -v -x` 遇到第一个失败立即停止

## 测试用例概览

### 接口测试（25 条）

| 模块 | 文件 | 数量 | 覆盖范围 |
|------|------|------|----------|
| Posts | `test_posts.py` | 11 | GET/POST/PUT/PATCH/DELETE、分页、筛选、评论关联 |
| Users | `test_users.py` | 7 | CRUD、Album 关联、Todo 关联 |
| Todos | `test_todos.py` | 7 | CRUD、completed 筛选、userId 筛选 |

**数据来源**：[JSONPlaceholder](https://jsonplaceholder.typicode.com) 免费测试 API

### 数据驱动测试（DDT）

| 模式 | 数据文件 | 覆盖范围 |
|------|----------|----------|
| 简单模式 | `data/sample_posts.csv` / `.xlsx` | POST /posts 批量创建 + 多字段断言 + 期望值反馈 |
| 通用模式 | `data/sample_generic.csv` | 任意 HTTP 方法/路径，JSON 期望响应 |

> 支持 `expect_fail` 列标记预期失败用例。失败时反馈类似：`字段 [title] 不匹配: 期望='X', 实际='Y'`

### UI 测试（15 条 · 3 个场景）

| 场景 | 文件 | 数量 | 覆盖范围 |
|------|------|------|----------|
| 登录流程 | `test_saucedemo_login.py` | 4 | 正常登录、锁定用户、空凭据、错误密码（参数化） |
| 购物流程 | `test_saucedemo_shopping.py` | 5 | 添加购物车、完整结算、移除商品、排序、继续购物 |
| 导航交互 | `test_saucedemo_navigation.py` | 6 | 商品详情、登出、重置状态、筛选、About、社交链接 |

**测试站点**：[Sauce Demo](https://www.saucedemo.com) 电商演示站

## 配置说明

编辑 `config/config.yaml`：

```yaml
# 环境切换 — 一键在 dev / test / staging / prod 之间切换
environment: test

# 接口配置
api:
  timeout: 30    # 请求超时（秒）
  retry: 3       # 失败自动重试次数

# UI 配置
ui:
  browser: chromium    # chromium / firefox / webkit
  headless: true       # true: 后台运行  false: 可见浏览器窗口
  viewport:
    width: 1920
    height: 1080

# 报告路径
report:
  allure_dir: "reports/allure-results"
  html_dir: "reports/html"
  screenshot_dir: "reports/screenshots"
```

### 多环境配置

```yaml
environments:
  test:                        # 当前使用
    api_base_url: "https://jsonplaceholder.typicode.com"
    ui_base_url: "https://www.saucedemo.com"
  prod:
    api_base_url: "https://api.example.com"
    ui_base_url: "https://www.example.com"
```

切换环境只需改 `environment` 字段的值，无需修改任何测试代码。

### 环境变量覆盖

支持通过环境变量覆盖配置（优先级高于 `config.yaml`）：

```bash
# 切换测试环境
export PYZDHU_ENV=staging

# 覆盖 API / UI 地址（CI/CD 中非常有用）
export PYZDHU_API_URL=https://my-api.example.com
export PYZDHU_UI_URL=https://my-app.example.com

# 同时设置后运行测试
pytest tests/api/ -v -m api
```

## 单元测试

框架自身及 Web 平台的单元测试（154 条），无需网络连接即可运行：

```bash
# 运行所有单元测试
python3 -m pytest tests/unit/ -v

# 按模块运行
python3 -m pytest tests/unit/test_config_loader.py -v
python3 -m pytest tests/unit/test_http_client.py -v
python3 -m pytest tests/unit/test_data_reader.py -v
python3 -m pytest tests/unit/test_data_driven.py -v
python3 -m pytest tests/unit/test_logger.py -v
python3 -m pytest tests/unit/test_utils.py -v
python3 -m pytest tests/unit/test_web_platform.py -v   # Web 平台后端逻辑
```

## 自定义标记

在测试用例上添加标记，实现按需筛选运行：

```python
@pytest.mark.smoke          # 冒烟测试 — 核心功能快速验证
@pytest.mark.api            # 接口测试
@pytest.mark.ui             # UI 测试
@pytest.mark.regression     # 回归测试
@pytest.mark.slow           # 慢速测试
```

运行示例：

```bash
pytest tests/ -v -m "smoke"                 # 只跑冒烟
pytest tests/ -v -m "smoke and api"         # 冒烟 + 接口
pytest tests/ -v -m "not slow"              # 排除慢速测试
```

> 标记需要在 `pytest.ini` 的 `markers` 中注册，否则会有警告。

## 核心特性

| 特性 | 说明 |
|------|------|
| 多环境 | `config.yaml` 一键切换 dev / test / staging / prod |
| HTTP 重试 | 请求失败自动重试（配置 `api.retry`，默认 3 次） |
| 失败截图 | UI 测试失败自动保存全页截图 |
| 失败堆栈 | 失败时自动将异常信息附加到 Allure 报告 |
| 参数化 | `@pytest.mark.parametrize` 覆盖多组输入数据 |
| 标记分类 | `smoke` / `api` / `ui` / `regression` 按需运行 |
| 并行执行 | `-n auto` 自动利用多核加速（接口测试） |
| HTML 报告 | pytest-html 自动生成（`--self-contained-html` 单文件） |
| Allure 报告 | 纯 Python 生成器，零额外依赖，带环境信息和分组展示 |
| 日志输出 | 终端实时显示测试日志（`log_cli = true`） |

## 常见问题

### Q: UI 测试报错 "Executable doesn't exist"?

浏览器未安装，执行：

```bash
playwright install chromium
```

### Q: 如何看到浏览器操作过程？

```bash
# 非无头模式 + 慢速
pytest tests/ui/ -v --headed --slowmo=500
```

### Q: 运行太快报错，如何降速？

Playwright 自动等待元素可见，如果仍有竞态问题，在用例中加 `page.wait_for_timeout(1000)` 或在配置中增大 `ui.timeout`。

### Q: 如何只跑最近失败的用例？

```bash
pytest tests/ --lf
```

### Q: Allure 报告和数据丢失？

运行测试确保带上 `--alluredir` 参数（`pytest.ini` 和 `run_tests.sh` 已默认配置），然后执行 `python3 generate_allure.py` 即可生成。

### Q: 接口测试的数据会真实写入吗？

不会。测试使用的是 [JSONPlaceholder](https://jsonplaceholder.typicode.com) 提供的模拟 API，POST/PUT/DELETE 请求会返回模拟结果但不会真实落库。
