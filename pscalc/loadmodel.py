"""负荷建模（M4）：恒功率负荷、同时率与负荷曲线。

设计阶段做短路/潮流时，负荷通常以「最大负荷 + 同时率」
给出；本模块统一这个口径：

  Load(p_mw, q_mvar, name)   单点负荷
  load_set(loads, coin)      同时率折算后的总负荷
  LoadCurve(hours, values)   日负荷曲线（24 点），
                             peak() / energy_mwh() / load_factor()
  scale_curve(curve, peak)   曲线整体缩放到指定峰值

M8 潮流取 LoadCurve.peak 的 P/Q 作为 PQ 节点注入。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Load:
    """恒功率负荷（P+jQ，MW/Mvar）。"""

    p_mw: float
    q_mvar: float
    name: str = "load"

    def __post_init__(self) -> None:
        if self.p_mw < 0:
            raise ValueError("负荷有功不能为负")


@dataclass(frozen=True)
class LoadCurve:
    """日负荷曲线：24 个整点值（MW）。"""

    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.values) != 24:
            raise ValueError("日负荷曲线必须 24 点")
        if any(v < 0 for v in self.values):
            raise ValueError("负荷曲线不能有负值")

    def peak(self) -> float:
        return max(self.values)

    def energy_mwh(self) -> float:
        return sum(self.values)

    def load_factor(self) -> float:
        """负荷率 = 平均/最大。"""
        peak = self.peak()
        if peak == 0:
            raise ValueError("全零曲线没有负荷率")
        return self.energy_mwh() / 24 / peak

    def value_at(self, hour: int) -> float:
        if not 0 <= hour <= 23:
            raise ValueError("小时取值 0-23")
        return self.values[hour]


def load_set(loads: list[Load], coincidence: float = 1.0) -> tuple[float, float]:
    """同时率折算后的总负荷 (P, Q)。

    coincidence=0.9 表示按 90% 同时率取总负荷。
    """
    if not 0 < coincidence <= 1:
        raise ValueError("同时率取值 (0, 1]")
    p = sum(ld.p_mw for ld in loads) * coincidence
    q = sum(ld.q_mvar for ld in loads) * coincidence
    return p, q


def scale_curve(curve: LoadCurve, peak_mw: float) -> LoadCurve:
    """曲线等比缩放到指定峰值（形状不变）。"""
    if peak_mw < 0:
        raise ValueError("目标峰值不能为负")
    old_peak = curve.peak()
    if old_peak == 0:
        return LoadCurve(tuple([peak_mw / 24] * 24))
    ratio = peak_mw / old_peak
    return LoadCurve(tuple(v * ratio for v in curve.values))


TYPICAL_DAY_SHAPE: tuple[float, ...] = (
    0.62, 0.58, 0.55, 0.54, 0.55, 0.60, 0.70, 0.82,
    0.88, 0.90, 0.92, 0.95, 0.90, 0.88, 0.90, 0.94,
    1.00, 0.98, 0.95, 0.92, 0.88, 0.80, 0.72, 0.66,
)
"""典型日形状（归一化到 1.0 峰值），scale_curve 前需乘以峰值。"""


def typical_curve(peak_mw: float) -> LoadCurve:
    """按典型日形状生成 24 点曲线。"""
    if peak_mw < 0:
        raise ValueError("峰值不能为负")
    return LoadCurve(tuple(v * peak_mw for v in TYPICAL_DAY_SHAPE))
