"""供电可靠性指标（M24）。

  saifi(...)        系统平均停电频率（次/户·年）
  saidi(...)        系统平均停电持续时间（时/户·年）
  caidi(...)        用户平均停电持续时间 = SAIDI/SAIFI
  asai(...)         供电可靠率 RS-1 = 1 - SAIDI/8760
  enr(...)          缺供电量（MWh）

事件口径：[(受影响用户数, 停电小时, 平均负荷 MW)]。
"""
from __future__ import annotations

from dataclasses import dataclass

HOURS_PER_YEAR = 8760.0


@dataclass(frozen=True)
class OutageEvent:
    """一次停电事件。"""

    customers: int
    hours: float
    avg_load_mw: float = 0.0

    def __post_init__(self) -> None:
        if self.customers < 0 or self.hours < 0 or self.avg_load_mw < 0:
            raise ValueError("事件参数不能为负")
        if self.customers == 0 and self.hours > 0:
            raise ValueError("无受影响用户的事件没有统计意义")


def saifi(events: list[OutageEvent], total_customers: int) -> float:
    """系统平均停电频率。"""
    if total_customers <= 0:
        raise ValueError("总用户数必须为正")
    return sum(e.customers for e in events) / total_customers


def saidi(events: list[OutageEvent], total_customers: int) -> float:
    """系统平均停电持续时间。"""
    if total_customers <= 0:
        raise ValueError("总用户数必须为正")
    return sum(e.customers * e.hours for e in events) / total_customers


def caidi(events: list[OutageEvent], total_customers: int) -> float:
    """用户平均停电持续时间 = SAIDI/SAIFI。"""
    f = saifi(events, total_customers)
    if f == 0:
        return 0.0
    return saidi(events, total_customers) / f


def asai(events: list[OutageEvent], total_customers: int) -> float:
    """供电可靠率（0-1）。"""
    d = saidi(events, total_customers)
    return 1 - d / HOURS_PER_YEAR


def enr(events: list[OutageEvent]) -> float:
    """缺供电量（MWh）= Σ 平均负荷 × 停电时长。"""
    return sum(e.avg_load_mw * e.hours for e in events)


def all_indices(
    events: list[OutageEvent], total_customers: int
) -> dict[str, float]:
    """一次算全套指标。"""
    return {
        "saifi": saifi(events, total_customers),
        "saidi": saidi(events, total_customers),
        "caidi": caidi(events, total_customers),
        "asai": asai(events, total_customers),
        "enr_mwh": enr(events),
    }
