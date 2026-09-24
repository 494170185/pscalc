"""数值工具（M29）：安全取值与格式化。

  clamp(...)              钳到区间
  safe_divide(...)        除零保护（返回 fallback）
  round_sig(...)          有效数字
  format_kv(...)          工程格式（kV/kA/MVA 带单位）

被各模块复用的纯函数集中放这里，避免散落。
"""
from __future__ import annotations


def clamp(value: float, lo: float, hi: float) -> float:
    """把 value 钳到 [lo, hi]。"""
    if lo > hi:
        raise ValueError("下限不能大于上限")
    return max(lo, min(hi, value))


def safe_divide(a: float, b: float, fallback: float = 0.0) -> float:
    """除零保护：b=0 返回 fallback。"""
    if b == 0:
        return fallback
    return a / b


def round_sig(value: float, digits: int = 3) -> float:
    """按有效数字舍入。"""
    if digits <= 0:
        raise ValueError("有效数字位数 ≥1")
    if value == 0:
        return 0.0
    import math

    exp = math.floor(math.log10(abs(value)))
    power = digits - 1 - exp
    return round(value, int(power))


def format_kv(value: float, unit: str, digits: int = 3) -> str:
    """工程数值格式：保留有效数字 + 单位。"""
    return f"{round_sig(value, digits):g} {unit}"
