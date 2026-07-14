#!/bin/bash
# ==========================================
# 自动化测试运行脚本
# ==========================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  自动化测试框架"
echo "=========================================="

# 安装依赖
install_deps() {
    echo ""
    echo "[1/2] 安装 Python 依赖..."
    pip install -r requirements.txt -q

    echo "[2/2] 安装 Playwright 浏览器..."
    python -m playwright install chromium --with-deps 2>/dev/null || playwright install chromium

    echo ""
    echo "✓ 环境准备完成"
}

# 公共参数
COMMON_ARGS="-v --self-contained-html --alluredir=reports/allure-results --clean-alluredir"

# 运行 API 测试
run_api() {
    echo ""
    echo "=========================================="
    echo "  运行接口测试 (API Tests)"
    echo "=========================================="
    pytest tests/api/ \
        $COMMON_ARGS \
        -m "api" \
        --html=reports/html/api_report.html \
        -n auto \
        2>&1 | tee reports/api_test_output.log
}

# 运行 UI 测试
run_ui() {
    echo ""
    echo "=========================================="
    echo "  运行 UI 测试 (UI Tests)"
    echo "=========================================="
    pytest tests/ui/ \
        $COMMON_ARGS \
        -m "ui" \
        --html=reports/html/ui_report.html \
        2>&1 | tee reports/ui_test_output.log
}

# 运行单元测试
run_unit() {
    echo ""
    echo "=========================================="
    echo "  运行单元测试 (Unit Tests)"
    echo "=========================================="
    echo "  无需网络连接，验证框架自身正确性"
    echo ""
    pytest tests/unit/ \
        -v \
        --tb=short \
        2>&1 | tee reports/unit_test_output.log
}

# 运行冒烟测试
run_smoke() {
    echo ""
    echo "=========================================="
    echo "  运行冒烟测试 (Smoke Tests)"
    echo "=========================================="
    pytest tests/ \
        $COMMON_ARGS \
        -m "smoke" \
        --html=reports/html/smoke_report.html \
        2>&1 | tee reports/smoke_test_output.log
}

# 运行全部测试
run_all() {
    echo ""
    echo "=========================================="
    echo "  运行全部测试"
    echo "=========================================="
    pytest tests/ \
        $COMMON_ARGS \
        --html=reports/html/full_report.html \
        -n auto \
        2>&1 | tee reports/full_test_output.log
}

# 跨平台打开文件
_open_file() {
    if command -v open >/dev/null 2>&1; then
        open "$1"
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$1"
    else
        echo "请手动打开: $1"
    fi
}

# 打开 HTML 报告
open_html() {
    echo ""
    echo "打开 HTML 报告..."
    REPORT_FILE="reports/html/${1:-report}.html"
    if [ -f "$REPORT_FILE" ]; then
        _open_file "$REPORT_FILE"
        echo "✓ 已打开: $REPORT_FILE"
    else
        echo "✗ 报告文件不存在: $REPORT_FILE"
        echo "  可用报告:"
        ls reports/html/ 2>/dev/null || echo "  (无)"
    fi
}

# 生成并打开 Allure 报告
allure_report() {
    echo ""
    echo "=========================================="
    echo "  生成 Allure 报告"
    echo "=========================================="
    if [ -d "reports/allure-results" ] && [ "$(ls -A reports/allure-results/*-result.json 2>/dev/null)" ]; then
        python3 generate_allure.py
        _open_file reports/allure-report/index.html
    else
        echo "✗ Allure 结果目录不存在或为空，请先运行测试"
        echo "  先执行: ./run_tests.sh api  或  ./run_tests.sh all"
    fi
}

# 清理报告
clean() {
    echo "清理测试报告..."
    rm -rf reports/html/* reports/allure-results/* reports/allure-report/* reports/screenshots/*
    echo "✓ 已清理"
}

# 主菜单
case "${1:-help}" in
    install)
        install_deps
        ;;
    unit)
        run_unit
        ;;
    api)
        run_api
        ;;
    ui)
        run_ui
        ;;
    smoke)
        run_smoke
        ;;
    all)
        run_all
        ;;
    clean)
        clean
        ;;
    html)
        open_html "${2:-report}"
        ;;
    allure)
        allure_report
        ;;
    help|*)
        echo ""
        echo "用法: ./run_tests.sh <命令>"
        echo ""
        echo "运行测试:"
        echo "  unit         运行单元测试（无需网络）"
        echo "  api          运行接口测试"
        echo "  ui           运行 UI 测试"
        echo "  smoke        运行冒烟测试"
        echo "  all          运行全部测试"
        echo ""
        echo "查看报告:"
        echo "  html [name]  打开 HTML 报告（默认 report）"
        echo "                可选: api_report, ui_report, smoke_report, full_report"
        echo "  allure       生成并打开 Allure 报告"
        echo ""
        echo "其他:"
        echo "  install      安装依赖和 Playwright 浏览器"
        echo "  clean        清理所有测试报告"
        echo ""
        ;;
esac

echo ""
echo "=========================================="
echo "  测试完成"
echo "=========================================="
