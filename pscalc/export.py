"""结果导出（M23）：短路/潮流结果 → CSV/JSON。

  fault_rows(...)       短路结果 → 行字典列表
  to_csv(...)           行字典列表 → CSV 文本
  to_json(...)          结果对象 → JSON 文本
  load_rows(...)        CSV 文本 → 行字典列表（回读校验用）

CSV 用标准库手写（零依赖约束），首行为表头。
"""
from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from typing import Any

from .shortcircuit import ShortCircuitResult

FAULT_FIELDS: list[str] = [
    "bus", "voltage_kv", "c", "r_pu", "x_pu",
    "ikss_ka", "ip_ka", "ib_ka", "ith_ka", "sk_mva",
]


def fault_rows(results: dict[str, ShortCircuitResult]) -> list[dict[str, Any]]:
    """短路结果转行字典（字段顺序按 FAULT_FIELDS）。"""
    rows: list[dict[str, Any]] = []
    for bus in sorted(results):
        r = results[bus]
        rows.append(
            {
                "bus": r.bus,
                "voltage_kv": r.voltage_kv,
                "c": r.c,
                "r_pu": r.r_pu,
                "x_pu": r.x_pu,
                "ikss_ka": r.ikss_ka,
                "ip_ka": r.ip_ka,
                "ib_ka": r.ib_ka,
                "ith_ka": r.ith_ka,
                "sk_mva": r.sk_mva,
            }
        )
    return rows


def to_csv(rows: list[dict[str, Any]]) -> str:
    """行字典列表 → CSV 文本（全部字段并集作表头）。"""
    if not rows:
        return ""
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def load_rows(csv_text: str) -> list[dict[str, str]]:
    """CSV 文本回读（数值字段保持字符串，由调用方转）。"""
    reader = csv.DictReader(io.StringIO(csv_text))
    return list(reader)


def to_json(obj: Any) -> str:
    """对象 → JSON 文本（dataclass 自动展开）。"""
    if hasattr(obj, "__dataclass_fields__"):
        payload: Any = asdict(obj)
    elif isinstance(obj, dict):
        payload = {
            k: asdict(v) if hasattr(v, "__dataclass_fields__") else v
            for k, v in obj.items()
        }
    else:
        payload = obj
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)
