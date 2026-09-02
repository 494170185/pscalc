"""电压调整系数 c 与峰值系数 κ（M1 收尾 / M7 使用）。

IEC 60909 的等效电压源用 c·Un/b³ 作为等值电压，c 按电压
等级与计算目的（最大/最小）取值；峰值系数 κ 由 R/X 决定。
"""
from __future__ import annotations

from .perunit import average_voltage

# IEC 60909-0 表 I：c_max。国内 110 kV 及以上取 1.1，
# 35 kV 及以下取 1.05（容差口径由 tolerance 参数显式给出）。
_C_MAX_LV = 37.0  # ≤35 kV 等级（Uq=37）用 c=1.05
_C_MAX_MV = 0.4  # 0.4 kV 等级用 c=1.05
_TOLERANCE_6 = 6.0  # 6% 电压偏差：低压系统 c=1.05 的容差口径
_TOLERANCE_10 = 10.0


def c_factor(kv: float, purpose: str = "max", tolerance: float | None = None) -> float:
    """电压调整系数 c（IEC 60909 表 I 的工程化取值）。

    purpose="max" 求最大短路电流（设备校验），"min" 求最小
    短路电流（保护灵敏度）。tolerance 显式给 6/10 时按
    c=1±t 口径调整低压侧取值。
    """
    uq = average_voltage(kv)
    if purpose not in ("max", "min"):
        raise ValueError("purpose 必须为 max 或 min")

    if tolerance is not None:
        if tolerance not in (_TOLERANCE_6, _TOLERANCE_10):
            raise ValueError("tolerance 只接受 6 或 10（%）")
        if purpose == "max":
            return 1 + tolerance / 100
        return 1 - tolerance / 100

    if purpose == "min":
        # 最小短路电流用无偏差额定电压
        return 1.0

    if uq <= _C_MAX_LV:
        # 35 kV 及以下（含 0.4）c_max=1.05
        return 1.05
    return 1.1


def kappa(r_over_x: float) -> float:
    """峰值系数 κ = 1.02 + 0.98·exp(-3·R/X)（IEC 60909 式 54）。

    R/X 为故障点处的等效比值。R/X<0 或过大时按 IEC 的保守
    近似（R/X=0 → κ=2.0）处理边界，负值直接报错。
    """
    if r_over_x < 0:
        raise ValueError("R/X 不能为负")
    k = 1.02 + 0.98 * pow(2.718281828459045, -3 * r_over_x)
    return min(k, 2.0)
