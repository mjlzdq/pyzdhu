"""
动态占位符引擎 - 支持变量池渲染与内置动态占位符
"""
import random
import re
import string
import time
import uuid as uuid_lib
from datetime import datetime
from typing import Any, Dict


def _render_dynamic_placeholders(text: str) -> str:
    """替换内置动态占位符"""
    if not isinstance(text, str):
        return text

    text = text.replace("{{uuid}}", str(uuid_lib.uuid4()))
    text = text.replace("{{uuid_short}}", str(uuid_lib.uuid4())[:8])
    text = text.replace("{{now}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    text = text.replace("{{date}}", datetime.now().strftime("%Y-%m-%d"))
    text = text.replace("{{timestamp}}", str(int(time.time())))

    for m in re.finditer(r'\{\{random_int(?::(\d+):(\d+))?\}\}', text):
        lo = int(m.group(1)) if m.group(1) else 0
        hi = int(m.group(2)) if m.group(2) else 999999
        text = text.replace(m.group(0), str(random.randint(lo, hi)))

    for m in re.finditer(r'\{\{random_str(?::(\d+))?\}\}', text):
        length = int(m.group(1)) if m.group(1) else 8
        text = text.replace(
            m.group(0),
            ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        )

    if "{{faker_email}}" in text:
        name = ''.join(random.choices(string.ascii_lowercase, k=8))
        text = text.replace("{{faker_email}}", f"{name}@autotest.com")

    if "{{faker_name}}" in text:
        first = random.choice("张李王赵陈刘杨黄周吴")
        last = random.choice("伟芳娜敏静强磊洋勇军")
        text = text.replace("{{faker_name}}", f"{first}{last}")

    if "{{faker_phone}}" in text:
        text = text.replace("{{faker_phone}}", f"1{random.randint(3,9)}{random.randint(100000000,999999999)}")

    return text


def _render_all_placeholders(data, pool: Dict[str, Any]) -> Any:
    """递归渲染变量池 {{var}} + 动态占位符"""
    if isinstance(data, str):
        for k, v in pool.items():
            data = data.replace(f"{{{{{k}}}}}", str(v))
        data = _render_dynamic_placeholders(data)
        return data
    elif isinstance(data, dict):
        return {k: _render_all_placeholders(v, pool) for k, v in data.items()}
    elif isinstance(data, list):
        return [_render_all_placeholders(item, pool) for item in data]
    return data
