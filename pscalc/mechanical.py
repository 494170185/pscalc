"""导线机械计算（M18）：弧垂与水平应力。

  sag(...)           等高悬点弧垂 f = w·L²/(8T)
  tension_at(...)    悬点应力 = T/cosθ 加垂直分量（简化口径）
  max_sag_span(...)  容许弧垂反算最大档距
  check_clearance(...) 对地/交叉跨越校验

单位：w（N/m）、L（m）、T（N）。比载由 caller 从
导线参数算（ice/wind 组合不在本模块）。
"""
from __future__ import annotations

from .equipment import EquipmentCheck


def sag(load_n_per_m: float, span_m: float, tension_n: float) -> float:
    """等高悬点弧垂（m）。"""
    if load_n_per_m <= 0 or span_m <= 0 or tension_n <= 0:
        raise ValueError("比载/档距/张力必须为正")
    return load_n_per_m * span_m**2 / (8 * tension_n)


def max_sag_span(load_n_per_m: float, tension_n: float, allowed_sag_m: float) -> float:
    """容许弧垂反算最大档距（m）。"""
    if allowed_sag_m <= 0:
        raise ValueError("容许弧垂必须为正")
    if load_n_per_m <= 0 or tension_n <= 0:
        raise ValueError("比载/张力必须为正")
    return (8 * tension_n * allowed_sag_m / load_n_per_m) ** 0.5


def support_tension(tension_n: float, load_n_per_m: float, span_m: float) -> float:
    """悬点最大张力（N）：水平张力 + 半档垂直荷载（简化口径）。"""
    if span_m < 0:
        raise ValueError("档距不能为负")
    vertical = load_n_per_m * span_m / 2
    return (tension_n**2 + vertical**2) ** 0.5


def check_clearance(
    sag_m: float, attachment_height_m: float, required_clearance_m: float
) -> EquipmentCheck:
    """对地距离校验：附件高度 − 弧垂 ≥ 要求距离。"""
    if attachment_height_m <= 0:
        raise ValueError("悬挂点高度必须为正")
    actual = attachment_height_m - sag_m
    ok = actual >= required_clearance_m
    if required_clearance_m > 0:
        margin = (actual / required_clearance_m - 1) * 100
    else:
        margin = float("inf")
    return EquipmentCheck(
        f"对地距离 {actual:.1f}m/{required_clearance_m:.1f}m", ok, margin
    )
