"""无功补偿（M10）：电容器组选型与效果核算。

  cap_bank_size(target_pf, p_mw, current_pf)   按目标功率
      因数反推所需补偿容量（kvar，工程式 Q=P·(tanφ₁-tanφ₂)）
  auto_config(q_need, unit_kvar, max_units)    分组方案：
      n 台 + 单台容量，贴近需求且不超过最大组数
  compensate_effect(...)                       补偿后功率因数/
      电压改善（与 M9 的 ΔU_X 口径衔接）

过补偿风险：补偿后功率因数超前（负 Q）时给出警示标记。
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CapConfig:
    """电容器组配置方案。"""

    units: int
    unit_kvar: float

    def total_kvar(self) -> float:
        return self.units * self.unit_kvar


def cap_bank_size(
    p_mw: float, current_pf: float, target_pf: float
) -> float:
    """所需补偿容量（kvar）。

    Q = P·(tanφ₁ - tanφ₂)；功率因数以绝对值给（超前/滞后
    由补偿量决定）。target > current 才需要补偿。
    """
    if p_mw <= 0:
        raise ValueError("有功功率必须为正")
    if not 0 < current_pf <= 1 or not 0 < target_pf <= 1:
        raise ValueError("功率因数取值 (0, 1]")
    if target_pf < current_pf:
        raise ValueError("目标功率因数应高于当前值")
    tan1 = math.tan(math.acos(current_pf))
    tan2 = math.tan(math.acos(target_pf))
    return p_mw * 1000 * (tan1 - tan2)


def auto_config(
    q_need_kvar: float, unit_kvar: float, max_units: int = 12
) -> CapConfig:
    """分组方案：n = ceil(Q/unit)，截到 max_units。"""
    if q_need_kvar < 0:
        raise ValueError("补偿需求不能为负")
    if unit_kvar <= 0 or max_units <= 0:
        raise ValueError("单台容量与最大组数必须为正")
    n = math.ceil(q_need_kvar / unit_kvar)
    n = min(n, max_units)
    return CapConfig(units=n, unit_kvar=unit_kvar)


@dataclass(frozen=True)
class CompensateEffect:
    """补偿效果核算。"""

    pf_after: float
    q_after_mvar: float
    over_compensated: bool

    def q_after_sign_hint(self) -> str:
        return "超前（进相）" if self.over_compensated else "滞后（迟相）"


def compensate_effect(
    p_mw: float, q_mvar: float, q_compensate_mvar: float
) -> CompensateEffect:
    """补偿后功率因数与剩余无功。

    over_compensated = 补偿后 Q<0（容性），报告要提示。
    """
    if p_mw <= 0:
        raise ValueError("有功功率必须为正")
    q_after = q_mvar - q_compensate_mvar
    s_after = math.hypot(p_mw, q_after)
    if s_after == 0:
        raise ValueError("补偿后视在功率为零")
    pf = p_mw / s_after
    return CompensateEffect(
        pf_after=pf,
        q_after_mvar=q_after,
        over_compensated=q_after < 0,
    )
