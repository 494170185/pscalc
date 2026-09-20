"""经济截面（M19）：按经济电流密度选导线截面。

  economic_section(i_a, hours, material)   J 表查值 → S = Imax/J
  annual_cost(...)                         年费用（TOC 简化）：
      投资年值 + 电能损耗费
  choose_conductor(...)                    从截面序列中选最优：
      先按经济截面粗选，再对邻档做年费用比较

经济电流密度 J（A/mm²）表（GB 50217 口径）：
铝：Tmax<3000h 取 1.92、3000-5000h 取 1.73、>5000h 取 1.54。
铜线分别是 2.50/2.25/2.00。
"""
from __future__ import annotations

from dataclasses import dataclass

_CURRENT_DENSITY: dict[str, tuple[float, float, float]] = {
    # 材质: (J_3000h以内, J_3000-5000h, J_5000h以上)
    "al": (1.92, 1.73, 1.54),
    "cu": (2.50, 2.25, 2.00),
}


def current_density(material: str, max_hours: float) -> float:
    """经济电流密度（A/mm²）。"""
    if material not in _CURRENT_DENSITY:
        raise ValueError("材质只支持 al/cu")
    if max_hours <= 0:
        raise ValueError("年最大负荷利用小时数必须为正")
    table = _CURRENT_DENSITY[material]
    if max_hours <= 3000:
        return table[0]
    if max_hours <= 5000:
        return table[1]
    return table[2]


def economic_section(imax_a: float, material: str, max_hours: float) -> float:
    """经济截面（mm²）：S = Imax/J。"""
    if imax_a <= 0:
        raise ValueError("最大电流必须为正")
    j = current_density(material, max_hours)
    return imax_a / j


@dataclass(frozen=True)
class CostParams:
    """年费用参数。"""

    investment_per_mm2: float  # 每毫米²截面投资（元/年·mm² 折算）
    loss_price_yuan_per_kwh: float
    resistance_per_mm2_km: float  # 单位截面单位长度电阻（Ω·mm²/km）
    hours_per_year: float = 8760.0

    def __post_init__(self) -> None:
        if self.investment_per_mm2 <= 0 or self.loss_price_yuan_per_kwh <= 0:
            raise ValueError("价格参数必须为正")
        if self.resistance_per_mm2_km <= 0:
            raise ValueError("单位电阻必须为正")


def annual_cost(
    section_mm2: float,
    imax_a: float,
    length_km: float,
    params: CostParams,
) -> float:
    """年费用（元）：投资年值 + 损耗费。

    损耗按最大电流全年运行（保守口径），实际损耗会除以
    负荷率平方——调用方自行折算输入 imax。
    """
    if section_mm2 <= 0 or length_km <= 0:
        raise ValueError("截面与长度必须为正")
    invest = section_mm2 * params.investment_per_mm2 * length_km
    r_ohm = params.resistance_per_mm2_km * length_km / section_mm2
    loss_kw = 3 * imax_a**2 * r_ohm / 1000
    loss_cost = loss_kw * params.hours_per_year * params.loss_price_yuan_per_kwh
    return invest + loss_cost


STANDARD_SECTIONS: tuple[float, ...] = (
    25, 35, 50, 70, 95, 120, 150, 185, 240, 300, 400,
)


def choose_conductor(
    imax_a: float,
    material: str,
    max_hours: float,
    length_km: float,
    params: CostParams,
) -> float:
    """从标准截面序列中选年费用最小的一档。

    只在「经济截面邻档」内比较（经济截面 ±1 档 + 按载流量
    上抬到满足最小档），避免全序列盲算。
    """
    s_econ = economic_section(imax_a, material, max_hours)
    candidates = [s for s in STANDARD_SECTIONS if s >= 0.6 * s_econ]
    if not candidates:
        candidates = [STANDARD_SECTIONS[-1]]
    # 截到 3 档
    idx = min(range(len(candidates)), key=lambda i: abs(candidates[i] - s_econ))
    lo, hi = max(0, idx - 1), min(len(candidates), idx + 2)
    window = candidates[lo:hi]
    best = min(window, key=lambda s: annual_cost(s, imax_a, length_km, params))
    return best
