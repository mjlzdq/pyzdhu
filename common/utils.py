"""
通用工具函数
"""
import re
from typing import Any

# 预编译路径分割正则，避免每次调用重复编译
_NESTED_PATH_RE = re.compile(r'(?<=\])\.|\.|(?=\[)')


def get_nested(data: Any, path: str) -> Any:
    """
    从嵌套的 dict / list 中按路径提取值。

    支持三种路径写法：
      - 点号分隔:        "data.user.name"
      - 方括号索引:      "data.list[0].status"
      - 点 + 方括号混合: "data.list[0].tags[1]"

    路径中任意节点不存在或类型不匹配时返回 None。

    Args:
        data: 嵌套结构（dict / list）
        path: 字段路径字符串
    """
    if not isinstance(data, (dict, list)) or not path:
        return None

    parts = _NESTED_PATH_RE.split(path)
    parts = [p for p in parts if p]

    cur = data
    for part in parts:
        if part.startswith('[') and part.endswith(']'):
            try:
                idx = int(part[1:-1])
            except ValueError:
                return None
            if isinstance(cur, list) and 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
            if cur is None:
                return None
        elif isinstance(cur, list):
            # 兼容 "0.name" 这类对列表直接用数字段索引的写法
            try:
                idx = int(part)
            except (ValueError, TypeError):
                return None
            if 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                return None
        else:
            return None
    return cur
