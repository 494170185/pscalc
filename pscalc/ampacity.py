"""载流量校正（M21）：环境温度与敷设方式修正。

  ambient_correction(...)    环境温度修正系数（线性插值表）
  grouping_correction(...)   多回路并敷修正
  derated_ampacity(...)      综合校正后载流量
  soil_correction(...)       直埋土壤热阻修正

修正表为公开手册典型值（空气中 25°C 基准）。
"""
from __future__ import annotations

import itertools

# 空气环境温度 → 修正系数（基准 25°C，XLPE 电缆）
_AMBIENT: dict[float, float] = {
    10: 1.11, 15: 1.07, 20: 1.04, 25: 1.00,
    30: 0.96, 35: 0.92, 40: 0.87, 45: 0.82,
}

# 并敷回路数 → 空中敷设修正
_GROUPING: dict[int, float] = {1: 1.00, 2: 0.92, 3: 0.87, 4: 0.82, 5: 0.78, 6: 0.75}


def ambient_correction(temp_c: float) -> float:
    """空气温度修正系数（线性插值，超出表范围钳到端点）。"""
    if temp_c < 0 or temp_c > 60:
        raise ValueError("环境温度取值 [0, 60] °C")
    keys = sorted(_AMBIENT)
    if temp_c <= keys[0]:
        return _AMBIENT[keys[0]]
    if temp_c >= keys[-1]:
        return _AMBIENT[keys[-1]]
    for lo, hi in itertools.pairwise(keys):
        if lo <= temp_c <= hi:
            f_lo, f_hi = _AMBIENT[lo], _AMBIENT[hi]
            t = (temp_c - lo) / (hi - lo)
            return f_lo + t * (f_hi - f_lo)
    raise AssertionError("unreachable")


def grouping_correction(circuits: int) -> float:
    """多回路并敷修正。1-6 回查表；>6 按 0.72（保守）。"""
    if circuits < 1:
        raise ValueError("回路数 ≥1")
    if circuits in _GROUPING:
        return _GROUPING[circuits]
    return 0.72


def derated_ampacity(
    rated_a: float,
    ambient_c: float = 25.0,
    circuits: int = 1,
    extra_factor: float = 1.0,
) -> float:
    """综合校正后载流量（A）。"""
    if rated_a <= 0:
        raise ValueError("额定载流量必须为正")
    if extra_factor <= 0 or extra_factor > 1.5:
        raise ValueError("附加系数取值 (0, 1.5]")
    return (
        rated_a
        * ambient_correction(ambient_c)
        * grouping_correction(circuits)
        * extra_factor
    )


def soil_correction(thermal_resistivity_kmk_per_w: float) -> float:
    """直埋土壤热阻修正（ρ=1.0 K·m/W 基准）。"""
    r = thermal_resistivity_kmk_per_w
    if r <= 0:
        raise ValueError("土壤热阻系数必须为正")
    if r < 0.7:
        return 1.05
    if r <= 1.0:
        return 1.0
    if r <= 1.5:
        return 0.93
    if r <= 2.0:
        return 0.87
    if r <= 2.5:
        return 0.82
    return 0.78
