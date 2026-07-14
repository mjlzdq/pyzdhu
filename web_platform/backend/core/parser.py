"""
数据解析模块 - 支持 CSV / XLSX 格式解析与自动 JSON 识别
"""
import csv
import io
import json
from typing import List, Dict

import openpyxl


def parse_csv(content: str) -> List[Dict]:
    """解析 CSV 内容，自动识别 JSON 字段，跳过全空行"""
    reader = csv.DictReader(io.StringIO(content))
    rows = []
    for row in reader:
        cleaned = {
            k.strip(): (v.strip() if isinstance(v, str) else v)
            for k, v in row.items()
        }
        if all(not v or (isinstance(v, str) and not v.strip()) for v in cleaned.values()):
            continue
        cleaned = _auto_parse_json(cleaned)
        rows.append(cleaned)
    return rows


def parse_xlsx(content: bytes) -> List[Dict]:
    """解析 XLSX 内容，第一行为表头"""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)

    headers = [
        str(h).strip() if h is not None else f"col_{i}"
        for i, h in enumerate(next(rows_iter))
    ]

    rows = []
    for row_values in rows_iter:
        if all(v is None for v in row_values):
            continue
        row = {}
        for i, header in enumerate(headers):
            val = row_values[i] if i < len(row_values) else ""
            row[header] = str(val).strip() if val is not None else ""
        row = _auto_parse_json(row)
        rows.append(row)

    wb.close()
    return rows


def _auto_parse_json(row: Dict) -> Dict:
    """自动将 JSON 字符串字段转为 dict/list"""
    for key in list(row.keys()):
        val = row[key]
        if isinstance(val, str) and (val.startswith("{") or val.startswith("[")):
            try:
                row[key] = json.loads(val)
            except (json.JSONDecodeError, ValueError):
                pass
    return row


def parse_file(content: bytes, filename: str = "") -> List[Dict]:
    """根据文件名自动识别格式并解析（CSV 或 XLSX）"""
    if filename.lower().endswith('.xlsx'):
        return parse_xlsx(content)
    # 默认按 CSV 处理（支持无 BOM 的 UTF-8）
    return parse_csv(content.decode("utf-8"))


def detect_format(filename: str) -> str:
    if filename.lower().endswith('.xlsx'):
        return 'xlsx'
    return 'csv'
