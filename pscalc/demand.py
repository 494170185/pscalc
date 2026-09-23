"""需侧负荷统计（M22）：需用系数法与二项式法。

  demand_method(...)       需用系数法：P30 = Σ(Kd·Pn)
  binomial_method(...)     二项式法：P30 = b·Ptop + c·Ptotal
  reactive_demand(...)     Q30 = P30·tanφ（按加权功率因数）
  demand_summary(...)      汇总：P/Q/S、需要系数核对

设备清单口径：[(名称, Pn_kW, Kd, cosφ)]。
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceLoad:
    """单台/单组设备的负荷参数。"""

    name: str
    pn_kw: float
    kd: float  # 需用系数
    cos_phi: float

    def __post_init__(self) -> None:
        if self.pn_kw < 0:
            raise ValueError("额定功率不能为负")
        if not 0 < self.kd <= 1:
            raise ValueError("需用系数取值 (0, 1]")
        if not 0 < self.cos_phi <= 1:
            raise ValueError("功率因数取值 (0, 1]")

    def demand_kw(self) -> float:
        return self.pn_kw * self.kd

    def reactive_kvar(self) -> float:
        return self.demand_kw() * math.tan(math.acos(self.cos_phi))


def demand_method(devices: list[DeviceLoad]) -> tuple[float, float]:
    """需用系数法计算 P30/Q30（kW/kvar）。"""
    if not devices:
        return 0.0, 0.0
    p = sum(d.demand_kw() for d in devices)
    q = sum(d.reactive_kvar() for d in devices)
    return p, q


def binomial_method(
    devices: list[DeviceLoad], b: float, c: float, top_n: int = 5
) -> float:
    """二项式法计算 P30（kW）。

    P30 = b·P_topN + c·P_total。top_n 台最大设备容量加总。
    b/c 系数由设备组性质决定（吊车/电焊类常用）。
    """
    if not devices:
        return 0.0
    if b < 0 or c < 0:
        raise ValueError("二项式系数不能为负")
    if top_n <= 0:
        raise ValueError("取最大设备台数 ≥1")
    p_total = sum(d.pn_kw for d in devices)
    top = sorted((d.pn_kw for d in devices), reverse=True)[:top_n]
    return b * sum(top) + c * p_total


def reactive_demand(p30_kw: float, cos_phi: float) -> float:
    """按综合功率因数折算无功。"""
    if p30_kw < 0:
        raise ValueError("有功不能为负")
    if not 0 < cos_phi <= 1:
        raise ValueError("功率因数取值 (0, 1]")
    return p30_kw * math.tan(math.acos(cos_phi))


@dataclass(frozen=True)
class DemandSummary:
    """负荷统计汇总。"""

    p30_kw: float
    q30_kvar: float
    s30_kva: float
    overall_pf: float


def demand_summary(devices: list[DeviceLoad]) -> DemandSummary:
    """汇总 P30/Q30/S30 与综合功率因数。"""
    p, q = demand_method(devices)
    s = math.hypot(p, q)
    pf = p / s if s > 0 else 1.0
    return DemandSummary(p30_kw=p, q30_kvar=q, s30_kva=s, overall_pf=pf)
