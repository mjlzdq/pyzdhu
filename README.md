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
│   └── logger.py                    # 统一日志工具
├── config/
│   └── config.yaml                  # 主配置文件（环境 / 超时 / 浏览器 等）
├── tests/
│   ├── __init__.py
│   ├── api/                         # 接口自动化测试
│   │   ├── __init__.py
│   │   ├── test_posts.py            #   文章 CRUD、筛选、评论（11 条）
│   │   ├── test_users.py            #   用户 CRUD、相册、待办（7 条）
│   │   └── test_todos.py            #   待办 CRUD、筛选（7 条）
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
| Python | 3.8+ |
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
