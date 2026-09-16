"""继电保护整定（M17）。

  instantaneous_pickup(...)   电流速断（Ⅰ段）：躲过末端最大三相短路
  timed_pickup(...)           限时速断（Ⅱ段）：与下级Ⅰ段配合
  overload_pickup(...)        过负荷（Ⅲ段）：躲最大负荷电流
  sensitivity(...)            灵敏度校验 Ksen = Ik.min/Iop
  relay_settings(...)         一次整定 → 二次侧（CT 变比）

整定原则按 GB/T 14285 的常规配合关系。
"""
from __future__ import annotations

from dataclasses import dataclass

from .equipment import EquipmentCheck


@dataclass(frozen=True)
class CTParams:
    """电流互感器变比（一次/二次）。"""

    primary_a: int
    secondary_a: int = 5

    def __post_init__(self) -> None:
        if self.primary_a <= 0 or self.secondary_a <= 0:
            raise ValueError("CT 变比必须为正")
        if self.primary_a <= self.secondary_a:
            raise ValueError("一次侧额定应大于二次侧")

    def ratio(self) -> float:
        return self.primary_a / self.secondary_a


def instantaneous_pickup(
    ik_max_end_ka: float, reliability: float = 1.3
) -> float:
    """电流速断整定值（kA）：躲过保护范围末端最大短路电流。"""
    if ik_max_end_ka <= 0:
        raise ValueError("末端短路电流必须为正")
    if reliability <= 1:
        raise ValueError("可靠系数应大于 1")
    return reliability * ik_max_end_ka


def timed_pickup(
    downstream_iop_ka: float,
    branch_factor: float = 1.0,
    reliability: float = 1.1,
) -> float:
    """限时速断（kA）：与下级速断配合，考虑分支系数。"""
    if downstream_iop_ka <= 0 or branch_factor <= 0:
        raise ValueError("下级整定值与分支系数必须为正")
    return reliability * branch_factor * downstream_iop_ka


def overload_pickup(
    iload_max_a: float, return_factor: float = 0.95, reliability: float = 1.2
) -> float:
    """过负荷整定（A）：躲最大负荷电流并考虑返回系数。"""
    if iload_max_a <= 0:
        raise ValueError("最大负荷电流必须为正")
    if not 0.8 <= return_factor <= 1.0:
        raise ValueError("返回系数取值 [0.8, 1.0]")
    return reliability * iload_max_a / return_factor


def sensitivity(ik_min_ka: float, pickup_ka: float) -> float:
    """灵敏度系数 Ksen = Ik.min / Iop。"""
    if pickup_ka <= 0:
        raise ValueError("整定值必须为正")
    if ik_min_ka < 0:
        raise ValueError("最小短路电流不能为负")
    return ik_min_ka / pickup_ka


def check_sensitivity(
    ik_min_ka: float, pickup_ka: float, minimum: float = 1.2
) -> EquipmentCheck:
    """灵敏度校验（主保护要求 1.5、后备 1.2，由调用方给 minimum）。"""
    ksen = sensitivity(ik_min_ka, pickup_ka)
    ok = ksen >= minimum
    margin = (ksen / minimum - 1) * 100 if minimum > 0 else float("inf")
    return EquipmentCheck(f"灵敏度 Ksen={ksen:.2f}", ok, margin)


def relay_settings(pickup_primary: float, ct: CTParams) -> float:
    """二次侧整定电流（A）= 一次整定 / CT 变比。"""
    return pickup_primary / ct.ratio()
