"""防雷保护范围（M16）：折线法与滚球法。

  rolling_sphere(...)   滚球法单支避雷针保护半径（GB 50057）
  protective_angle(...) 保护角法（IEC 62305 简化）
  zone_overlap(...)     两针联合保护的中线高度

滚球半径按建筑类别：一类 30 m、二类 45 m、三类 60 m。
"""
from __future__ import annotations

from dataclasses import dataclass

CLASS_ROLLING_RADIUS = {1: 30.0, 2: 45.0, 3: 60.0}


@dataclass(frozen=True)
class MastConfig:
    """避雷针参数：高度 h（m）与建筑类别（1/2/3）。"""

    height_m: float
    building_class: int = 2

    def __post_init__(self) -> None:
        if self.height_m <= 0:
            raise ValueError("避雷针高度必须为正")
        if self.building_class not in CLASS_ROLLING_RADIUS:
            raise ValueError("建筑类别取 1/2/3")


def rolling_radius(building_class: int) -> float:
    """滚球半径（m）。"""
    if building_class not in CLASS_ROLLING_RADIUS:
        raise ValueError("建筑类别取 1/2/3")
    return CLASS_ROLLING_RADIUS[building_class]


def rolling_sphere(mast: MastConfig, height_above_ground: float = 0.0) -> float:
    """滚球法：在给定被保护物高度上的保护半径（m）。

    rx = √(h(2R−h)) − √(hx(2R−hx))；h≤R。h>R 时保守取 R 口径。
    """
    r = rolling_radius(mast.building_class)
    h = min(mast.height_m, r)
    if height_above_ground < 0 or height_above_ground > r:
        raise ValueError("被保护物高度超出滚球半径范围")
    term1 = (h * (2 * r - h)) ** 0.5
    hx = min(height_above_ground, r)
    term2 = (hx * (2 * r - hx)) ** 0.5
    return term1 - term2


def protective_angle(mast: MastConfig, angle_deg: float) -> float:
    """保护角法：针尖以下某高度的保护半径 = h·tan(α)。"""
    if not 0 < angle_deg < 90:
        raise ValueError("保护角取值 (0, 90)")
    import math

    return (mast.height_m - 0.0) * math.tan(math.radians(angle_deg))


def zone_overlap(mast1: MastConfig, mast2: MastConfig, distance_m: float) -> float:
    """两针联合保护：两针间中点保护宽度（m）。

    简化口径：每针保护半径取 0.7·rx（地面），中点宽度 =
    2·√(D/2·(rx_avg−D/2))；D > rx_avg 时无联合保护返回 0。
    """
    if distance_m <= 0:
        raise ValueError("针间距必须为正")
    rx1 = rolling_sphere(mast1)
    rx2 = rolling_sphere(mast2)
    rx_avg = 0.7 * (rx1 + rx2) / 2
    half_d = distance_m / 2
    if rx_avg <= half_d:
        return 0.0
    return 2 * (half_d * (rx_avg - half_d)) ** 0.5
