#!/usr/bin/env python3
"""
Allure 报告生成器（纯 Python，无需 allure 命令行）
读取 allure-results/*-result.json 生成 HTML 报告
"""
import html
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict


def collect_results(results_dir: str) -> list:
    """收集所有测试结果"""
    results = []
    for file in sorted(Path(results_dir).glob("*-result.json")):
        try:
            with open(file, "r", encoding="utf-8") as f:
                results.append(json.load(f))
        except Exception as e:
            print(f"警告: 无法解析 {file.name}: {e}")
    return results


def format_duration(ms: int) -> str:
    """格式化耗时"""
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms / 1000:.1f}s"
    else:
        return f"{ms / 60000:.1f}min"


def render_report(results: list, env_info: dict, dest: str):
    """渲染 HTML 报告"""
    # 统计数据
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    broken = sum(1 for r in results if r.get("status") == "broken")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    total_duration = sum(r.get("time", {}).get("duration", 0) for r in results)

    # 按标签分组
    groups = defaultdict(list)
    for r in results:
        labels = {l["name"]: l["value"] for l in r.get("labels", [])}
        feature = labels.get("feature", "未分类")
        groups[feature].append(r)

    # 状态颜色
    status_colors = {
        "passed": "#28a745", "failed": "#dc3545",
        "broken": "#ffc107", "skipped": "#6c757d",
    }
    status_icons = {
        "passed": "✅", "failed": "❌",
        "broken": "⚠️", "skipped": "⏭️",
    }

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Allure 测试报告</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; color: #2d3436; }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 40px; }}
.header h1 {{ font-size: 28px; font-weight: 600; }}
.header .meta {{ margin-top: 8px; opacity: 0.85; font-size: 14px; }}
.summary {{ display: flex; gap: 20px; padding: 25px 40px; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.06); flex-wrap: wrap; }}
.summary-card {{ flex: 1; min-width: 120px; text-align: center; padding: 20px; border-radius: 12px; background: #f8f9fa; }}
.summary-card .count {{ font-size: 36px; font-weight: 700; }}
.summary-card .label {{ font-size: 13px; color: #636e72; margin-top: 4px; }}
.summary-card.passed .count {{ color: #28a745; }}
.summary-card.failed .count {{ color: #dc3545; }}
.summary-card.broken .count {{ color: #e17055; }}
.summary-card.skipped .count {{ color: #6c757d; }}
.summary-card.duration .count {{ color: #0984e3; font-size: 24px; }}
.env-info {{ padding: 20px 40px; background: white; border-top: 1px solid #eee; display: flex; flex-wrap: wrap; gap: 20px; font-size: 13px; color: #636e72; }}
.env-info strong {{ color: #2d3436; }}
.content {{ padding: 20px 40px 40px; }}
.feature {{ margin-bottom: 30px; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
.feature-header {{ padding: 15px 25px; background: #f8f9fa; font-size: 16px; font-weight: 600; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
.feature-header .badge {{ font-size: 12px; padding: 4px 12px; border-radius: 20px; background: #dfe6e9; color: #636e72; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 12px 20px; text-align: left; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
th {{ background: #fafafa; font-weight: 600; color: #636e72; font-size: 12px; text-transform: uppercase; }}
tr:hover {{ background: #f8f9ff; }}
.status-badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
.name-cell {{ font-weight: 500; }}
.duration-cell {{ color: #636e72; font-size: 13px; }}
.fail-reason {{ font-size: 12px; color: #d63031; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.progress-bar {{ height: 8px; border-radius: 4px; background: #eee; margin-top: 12px; overflow: hidden; display: flex; }}
.progress-passed {{ background: #28a745; height: 100%; }}
.progress-failed {{ background: #dc3545; height: 100%; }}
.progress-broken {{ background: #e17055; height: 100%; }}
.progress-skipped {{ background: #6c757d; height: 100%; }}
.footer {{ text-align: center; padding: 20px; color: #b2bec3; font-size: 12px; }}
</style>
</head>
<body>

<div class="header">
    <h1>📊 Allure 测试报告</h1>
    <div class="meta">生成时间: {now}</div>
</div>

<div class="summary">
    <div class="summary-card duration">
        <div class="count">{format_duration(total_duration)}</div>
        <div class="label">总耗时</div>
    </div>
    <div class="summary-card">
        <div class="count">{total}</div>
        <div class="label">总计</div>
    </div>
    <div class="summary-card passed">
        <div class="count">{passed}</div>
        <div class="label">✅ 通过</div>
    </div>
    <div class="summary-card failed">
        <div class="count">{failed}</div>
        <div class="label">❌ 失败</div>
    </div>
    <div class="summary-card broken">
        <div class="count">{broken}</div>
        <div class="label">⚠️ 异常</div>
    </div>
    <div class="summary-card skipped">
        <div class="count">{skipped}</div>
        <div class="label">⏭️ 跳过</div>
    </div>
</div>

<div class="progress-bar">
    <div class="progress-passed" style="width:{passed/max(total,1)*100:.1f}%"></div>
    <div class="progress-failed" style="width:{failed/max(total,1)*100:.1f}%"></div>
    <div class="progress-broken" style="width:{broken/max(total,1)*100:.1f}%"></div>
    <div class="progress-skipped" style="width:{skipped/max(total,1)*100:.1f}%"></div>
</div>

<div class="env-info">
    {''.join(f'<span><strong>{k}:</strong> {v}</span>' for k, v in env_info.items()) if env_info else '<span>无环境信息</span>'}
</div>

<div class="content">
"""

    # 按分组渲染
    for feature, items in groups.items():
        f_passed = sum(1 for r in items if r.get("status") == "passed")
        f_total = len(items)
        html += f"""
<div class="feature">
    <div class="feature-header">
        <span>{feature}</span>
        <span class="badge">{f_passed}/{f_total} 通过</span>
    </div>
    <table>
        <thead>
            <tr><th>状态</th><th>用例名称</th><th>耗时</th><th>失败原因</th></tr>
        </thead>
        <tbody>
"""
        for r in items:
            name = r.get("name", "未命名")
            status = r.get("status", "unknown")
            duration = r.get("time", {}).get("duration", 0)
            status_msg = r.get("statusDetails", {}).get("message", "")
            trace = r.get("statusDetails", {}).get("trace", "")

            icon = status_icons.get(status, "❓")
            color = status_colors.get(status, "#333")

            fail_info = ""
            if status in ("failed", "broken"):
                safe_msg = html.escape(status_msg)
                safe_title = safe_msg.replace("\n", " ").replace("\r", "")[:500]
                fail_info = f'<div class="fail-reason" title="{safe_title}">{safe_msg[:80]}</div>'

            safe_name = html.escape(name)
            html += f"""
            <tr>
                <td><span class="status-badge" style="background:{color}20;color:{color}">{icon} {status}</span></td>
                <td class="name-cell">{safe_name}</td>
                <td class="duration-cell">{format_duration(duration)}</td>
                <td>{fail_info}</td>
            </tr>"""

        html += """
        </tbody>
    </table>
</div>"""

    html += """
</div>
<div class="footer">
    Powered by Python Allure Report Generator | Pytest + Allure-Pytest
</div>
</body>
</html>"""

    # 写入文件
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html)


def load_env_info(results_dir: str) -> dict:
    """加载环境信息"""
    env_file = Path(results_dir) / "environment.properties"
    info = {}
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    info[k] = v
    return info


def main():
    results_dir = "reports/allure-results"
    dest = "reports/allure-report/index.html"

    # 支持命令行参数
    if len(sys.argv) >= 2:
        results_dir = sys.argv[1]
    if len(sys.argv) >= 3:
        dest = sys.argv[2]

    if not Path(results_dir).exists():
        print(f"错误: 目录不存在 - {results_dir}")
        sys.exit(1)

    results = collect_results(results_dir)
    if not results:
        print(f"警告: {results_dir} 中没有找到测试结果文件")
        print("请先运行测试: python3 -m pytest tests/ --alluredir=reports/allure-results")
        sys.exit(1)

    env_info = load_env_info(results_dir)
    render_report(results, env_info, dest)

    print(f"✅ Allure 报告已生成: {dest}")
    print(f"   共 {len(results)} 条测试结果")


if __name__ == "__main__":
    main()
