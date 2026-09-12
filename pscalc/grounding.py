"""接地网计算（M15）。

  grid_resistance(...)        水平接地网工频电阻（两项式）
  allowable_touch(...)        允许接触电压（IEEE 80, 50 kg 口径）
  allowable_step(...)         允许跨步电压
  gpr(...)                    地电位升 Ig·Rg
  check_grounding(...)        校验链：Rg、接触、跨步（复用 EquipmentCheck）

两项式：Rg = ρ/(4r) + ρ/L，r=√(A/π)。允许值：
Et = (116+0.174ρs)/√t；Es = (116+0.696ρs)/√t。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .equipment import EquipmentCheck


@dataclass(frozen=True)
class GridParams:
    """水平接地网参数。"""

    area_m2: float
    total_length_m: float  # 埋地导体总长（含均压带）
    depth_m: float = 0.8

    def __post_init__(self) -> None:
        if self.area_m2 <= 0 or self.total_length_m <= 0 or self.depth_m <= 0:
            raise ValueError("接地网几何参数必须为正")


def grid_resistance(rho_ohm_m: float, grid: GridParams) -> float:
    """工频接地电阻（Ω）：Rg = ρ/(4r) + ρ/L。"""
    if rho_ohm_m <= 0:
        raise ValueError("土壤电阻率必须为正")
    r = math.sqrt(grid.area_m2 / math.pi)
    return rho_ohm_m / (4 * r) + rho_ohm_m / grid.total_length_m


def allowable_touch(rho_s: float, t_s: float, weight: str = "50kg") -> float:
    """允许接触电压（V）。weight 选 "50kg"/"70kg" 的人体口径。"""
    if rho_s < 0 or t_s <= 0:
        raise ValueError("参数非法")
    base = 116.0 if weight == "50kg" else 157.0
    coef = 0.174 if weight == "50kg" else 0.236
    return (base + coef * rho_s) / math.sqrt(t_s)


def allowable_step(rho_s: float, t_s: float, weight: str = "50kg") -> float:
    """允许跨步电压（V）。"""
    if rho_s < 0 or t_s <= 0:
        raise ValueError("参数非法")
    base = 116.0 if weight == "50kg" else 157.0
    coef = 0.696 if weight == "50kg" else 0.944
    return (base + coef * rho_s) / math.sqrt(t_s)


def gpr(ig_a: float, rg_ohm: float) -> float:
    """地电位升（V）：GPR = Ig·Rg。"""
    if ig_a < 0 or rg_ohm < 0:
        raise ValueError("电流与电阻不能为负")
    return ig_a * rg_ohm


def check_grounding(
    rho_ohm_m: float,
    grid: GridParams,
    ig_a: float,
    est_touch_v: float,
    est_step_v: float,
    rho_s: float,
    t_s: float,
    target_rg_ohm: float | None = None,
) -> list[EquipmentCheck]:
    """接地校验：Rg（给了目标值时）、接触电压、跨步电压。

    est_touch_v / est_step_v 为估计的最大接触/跨步电压
    （由短路电流与均压网几何系数算出，几何系数不在本模块）。
    """
    checks: list[EquipmentCheck] = []
    rg = grid_resistance(rho_ohm_m, grid)
    if target_rg_ohm is not None:
        ok = rg <= target_rg_ohm
        margin = (target_rg_ohm / rg - 1) * 100 if rg > 0 else float("inf")
        checks.append(EquipmentCheck(f"接地电阻 Rg={rg:.2f}Ω", ok, margin))
    at = allowable_touch(rho_s, t_s)
    ok = est_touch_v <= at
    margin = (at / est_touch_v - 1) * 100 if est_touch_v > 0 else float("inf")
    checks.append(EquipmentCheck(f"接触电压 {est_touch_v:.0f}V/{at:.0f}V", ok, margin))
    asv = allowable_step(rho_s, t_s)
    ok = est_step_v <= asv
    margin = (asv / est_step_v - 1) * 100 if est_step_v > 0 else float("inf")
    checks.append(EquipmentCheck(f"跨步电压 {est_step_v:.0f}V/{asv:.0f}V", ok, margin))
    _ = gpr(ig_a, rg)  # GPR 供报告引用，不单独判据
    return checks
