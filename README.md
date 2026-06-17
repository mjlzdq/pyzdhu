# 自动化测试框架

基于 **Pytest + Requests + Playwright** 的 Python 自动化测试框架，支持接口测试和 UI 测试。

## 项目结构

```
pyzdhu/
├── common/                    # 公共模块
│   ├── config_loader.py       # 配置加载器（多环境）
│   ├── http_client.py         # HTTP 请求客户端（重试机制）
│   └── logger.py              # 日志工具
├── config/
│   └── config.yaml            # 配置文件（环境/超时/浏览器等）
├── tests/
│   ├── api/                   # 接口测试
│   │   ├── test_posts.py      # 文章 CRUD（11 条用例）
│   │   ├── test_users.py      # 用户 CRUD（7 条用例）
│   │   └── test_todos.py      # 待办 CRUD（7 条用例）
│   └── ui/                    # UI 测试
│       ├── conftest.py        # Playwright fixtures + 失败截图
│       ├── test_saucedemo_login.py     # 场景1: 登录流程
│       ├── test_saucedemo_shopping.py  # 场景2: 购物流程
│       └── test_saucedemo_navigation.py # 场景3: 导航交互
├── reports/                   # 测试报告输出
│   ├── html/                  #   HTML 报告
│   ├── allure-results/        #   Allure 原始数据
│   ├── allure-report/         #   Allure 静态报告
│   └── screenshots/           #   失败截图
├── conftest.py                # 全局 Pytest 夹具 + Allure 集成
├── pytest.ini                 # Pytest 配置
├── requirements.txt           # 依赖清单
├── run_tests.sh               # 一键运行脚本
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

或一键安装：

```bash
./run_tests.sh install
```

### 2. 运行测试

```bash
# 运行接口测试（25 条用例）
./run_tests.sh api

# 运行 UI 测试（15 条用例）
./run_tests.sh ui

# 运行冒烟测试
./run_tests.sh smoke

# 运行全部测试
./run_tests.sh all
```

也可以直接使用 pytest：

```bash
# 接口测试（同时生成 HTML + Allure 数据）
pytest tests/api/ -v -m api \
    --html=reports/html/api_report.html --self-contained-html \
    --alluredir=reports/allure-results --clean-alluredir

# UI 测试
pytest tests/ui/ -v -m ui \
    --html=reports/html/ui_report.html --self-contained-html \
    --alluredir=reports/allure-results --clean-alluredir

# 指定单个文件
pytest tests/api/test_posts.py -v \
    --html=reports/html/report.html --self-contained-html \
    --alluredir=reports/allure-results --clean-alluredir
```

### 3. 查看报告

#### HTML 报告

```bash
# 通过脚本打开
./run_tests.sh html api_report

# 或直接打开文件
open reports/html/api_report.html
open reports/html/ui_report.html
open reports/html/smoke_report.html
open reports/html/full_report.html
```

#### Allure 报告（纯 Python 生成，无需安装额外工具）

```bash
# 生成并打开 Allure 报告
./run_tests.sh allure

# 或手动生成
python3 generate_allure.py
open reports/allure-report/index.html
```

## 测试用例概览

### 接口测试（25 条）

| 模块 | 文件 | 用例数 | 覆盖 |
|------|------|--------|------|
| Posts | `test_posts.py` | 11 | GET/POST/PUT/PATCH/DELETE、分页、筛选、评论关联 |
| Users | `test_users.py` | 7 | CRUD、相册关联、待办关联 |
| Todos | `test_todos.py` | 7 | CRUD、完成状态筛选、用户筛选 |

### UI 测试（15 条）- 3 个场景

| 场景 | 文件 | 用例数 | 覆盖 |
|------|------|--------|------|
| 登录 | `test_saucedemo_login.py` | 4 | 正常登录、锁定用户、空凭据、错误密码参数化 |
| 购物 | `test_saucedemo_shopping.py` | 5 | 添加购物车、完整结算、移除商品、排序、继续购物 |
| 导航 | `test_saucedemo_navigation.py` | 6 | 商品详情、登出、重置状态、筛选、About、社交链接 |

## 核心特性

- **多环境支持**：通过 `config/config.yaml` 切换 dev/test/staging/prod
- **HTTP 重试机制**：请求失败自动重试（默认 3 次）
- **失败自动截图**：UI 测试失败自动保存全页截图到 `reports/screenshots/`
- **参数化测试**：使用 `@pytest.mark.parametrize` 覆盖多种输入
- **测试标记**：`smoke` / `api` / `ui` / `regression` 分类运行
- **并行执行**：`-n auto` 自动利用多核加速
- **HTML 报告**：`--html` 生成可视化测试报告
- **Allure 报告**：环境信息 + 失败截图 + 分类筛选 + 趋势图

## 自定义标记

```python
@pytest.mark.smoke      # 冒烟测试
@pytest.mark.api        # 接口测试
@pytest.mark.ui         # UI 测试
@pytest.mark.regression # 回归测试
```

## 配置说明

编辑 `config/config.yaml`：

```yaml
environment: test  # 切换环境

ui:
  browser: chromium   # chromium / firefox / webkit
  headless: true      # false 可看到浏览器运行

api:
  timeout: 30         # 请求超时（秒）
  retry: 3            # 重试次数
```
