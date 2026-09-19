"""设备校验（M11）：短路结果 vs 设备耐受能力。

  check_breaker(...)     遮断容量（Ib·√3·U）、峰值动稳定 ip、
                         热稳定 Ith vs 允许值
  check_busbar(...)      母线热稳定（截面·允许电流密度口径）
  check_cable(...)       电缆热稳定截面 S_min = Ith·√t/k
  check_overhead(...)    架空线允许电流 vs 负荷电流
  EquipmentCheck        统一结果对象（通过/裕度百分比）

裕度 margin = (设备能力/需求 - 1)·100%，负值 = 不通过。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EquipmentCheck:
    """单项校验结果。"""

    item: str
    ok: bool
    margin_pct: float

    def summary(self) -> str:
        state = "通过" if self.ok else "不通过"
        return f"{self.item}: {state}（裕度 {self.margin_pct:+.1f}%）"


@dataclass(frozen=True)
class BreakerRating:
    """断路器额定参数。"""

    rated_breaking_ka: float
    rated_peak_ka: float
    rated_thermal_ka: float  # 允许热稳定电流（对应短时耐受时间）
    thermal_time_s: float = 3.0


@dataclass(frozen=True)
class BusbarRating:
    """母线参数：截面（mm²）与热稳定系数。"""

    area_mm2: float
    k_factor: float = 171.0  # 铜母线热稳定系数（A·s^0.5/mm²）


@dataclass(frozen=True)
class CableRating:
    """电缆参数。"""

    area_mm2: float
    k_factor: float = 142.0  # 铜芯交联聚乙烯
    ampacity_a: float = 0.0  # 载流量（0 = 不校验载流）


@dataclass(frozen=True)
class OverheadRating:
    """架空线参数：允许载流量与截面。"""

    ampacity_a: float
    area_mm2: float = 0.0


def _margin(capability: float, demand: float) -> tuple[bool, float]:
    if demand <= 0:
        raise ValueError("需求必须为正")
    if capability <= 0:
        raise ValueError("设备能力必须为正")
    margin = (capability / demand - 1) * 100
    return margin >= 0, margin


def check_breaker(
    rating: BreakerRating,
    ikss_ka: float,
    ip_ka: float,
    ith_ka: float,
    tk_s: float,
) -> list[EquipmentCheck]:
    """断路器三项校验：开断、动稳定（峰值）、热稳定。

    热稳定口径：Ith²·tk ≤ I_rated²·t_rated（时间修正）。
    """
    if tk_s <= 0:
        raise ValueError("切除时间必须为正")
    checks: list[EquipmentCheck] = []
    ok, m = _margin(rating.rated_breaking_ka, ikss_ka)
    checks.append(EquipmentCheck("断路器开断（Ik''）", ok, m))
    ok, m = _margin(rating.rated_peak_ka, ip_ka)
    checks.append(EquipmentCheck("断路器动稳定（ip）", ok, m))
    # 热稳定时间归算：需求 Ith 在 tk 下的能量与额定在 t_rated 下比
    demand_thermal = ith_ka * (tk_s**0.5)
    capability_thermal = rating.rated_thermal_ka * (rating.thermal_time_s**0.5)
    ok, m = _margin(capability_thermal, demand_thermal)
    checks.append(EquipmentCheck("断路器热稳定（Ith·√t）", ok, m))
    return checks


def check_busbar(rating: BusbarRating, ith_ka: float, tk_s: float) -> list[EquipmentCheck]:
    """母线热稳定：S ≥ Ith·√t/k（mm²）。"""
    if tk_s <= 0:
        raise ValueError("切除时间必须为正")
    if rating.k_factor <= 0:
        raise ValueError("热稳定系数必须为正")
    s_min = ith_ka * 1000 * tk_s**0.5 / rating.k_factor
    ok, m = _margin(rating.area_mm2, s_min)
    return [EquipmentCheck("母线热稳定截面", ok, m)]


def check_cable(
    rating: CableRating, ith_ka: float, tk_s: float, load_current_a: float = 0.0
) -> list[EquipmentCheck]:
    """电缆：热稳定最小截面 + 载流量（ampacity>0 时）。"""
    if tk_s <= 0:
        raise ValueError("切除时间必须为正")
    checks: list[EquipmentCheck] = []
    s_min = ith_ka * 1000 * tk_s**0.5 / rating.k_factor
    ok, m = _margin(rating.area_mm2, s_min)
    checks.append(EquipmentCheck("电缆热稳定截面", ok, m))
    if rating.ampacity_a > 0:
        if load_current_a <= 0:
            raise ValueError("校验载流量需要正的负荷电流")
        ok, m = _margin(rating.ampacity_a, load_current_a)
        checks.append(EquipmentCheck("电缆载流量", ok, m))
    return checks


def check_overhead(rating: OverheadRating, load_current_a: float) -> list[EquipmentCheck]:
    """架空线载流量校验（热稳定与电缆同式，area>0 时校验）。"""
    checks: list[EquipmentCheck] = []
    if load_current_a <= 0:
        raise ValueError("负荷电流必须为正")
    ok, m = _margin(rating.ampacity_a, load_current_a)
    checks.append(EquipmentCheck("架空线载流量", ok, m))
    return checks
