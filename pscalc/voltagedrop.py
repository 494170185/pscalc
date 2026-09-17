"""电压损耗与调压（M9）。

  voltage_drop(res, bus)      潮流结果的电压损耗 ΔU%（对首端）
  drop_components(...)        R/X 分解：ΔU_R 与 ΔU_X 两项
  regulation_advice(...)      按目标电压反推需要的无功补偿量/
                              分接调整步数

工程口径：10 kV 母线允许 7%（+），35 kV 及以上 10%。
"""
from __future__ import annotations

from dataclasses import dataclass

from .powerflow import PowerFlowResult


@dataclass(frozen=True)
class DropComponents:
    """电压损耗的 R/X 贡献分解（pu）。"""

    du_r: float
    du_x: float

    def total(self) -> float:
        return self.du_r + self.du_x


def voltage_drop(res: PowerFlowResult, bus: str, slack: str = "G") -> float:
    """bus 相对 slack 的电压损耗百分数（正值 = 下降）。"""
    if bus not in res.voltages or slack not in res.voltages:
        raise KeyError("母线不在潮流结果里")
    v_slack = res.voltages[slack]
    if v_slack == 0:
        raise ValueError("平衡节点电压为零")
    return (1 - res.voltages[bus] / v_slack) * 100


def drop_components(res: PowerFlowResult, branch_index: int) -> DropComponents:
    """按支路功率分解 ΔU = (P·R+Q·X)/U²。

    branch_index 指向 res.branch_flows 列表。
    """
    fl = res.branch_flows[branch_index]
    if fl.p_from_mw == 0 and fl.q_from_mvar == 0:
        return DropComponents(du_r=0.0, du_x=0.0)
    # 用 pu：功率/100MVA；阻抗 pu 直接取——这里从结果反推
    # 需要 R/X，潮流结果没存支路阻抗，改由调用方给（见 docstring）
    raise NotImplementedError("改用 drop_from_impedance")


def drop_from_impedance(
    p_mw: float, q_mvar: float, r_pu: float, x_pu: float, u_pu: float = 1.0
) -> DropComponents:
    """ΔU% 的 R/X 分解（pu 口径，直接给参数）。"""
    if u_pu <= 0:
        raise ValueError("电压必须为正")
    s_pu = complex(p_mw, q_mvar) / 100.0
    # ΔU ≈ (P·R + Q·X)/U（pu），以 100 MVA 为基准
    du_r = (s_pu.real * r_pu) / u_pu
    du_x = (s_pu.imag * x_pu) / u_pu
    return DropComponents(du_r=du_r, du_x=du_x)


@dataclass(frozen=True)
class RegulationAdvice:
    """调压建议：需要的补偿量与分接步数。"""

    need_q_mvar: float
    tap_steps: float
    current_drop_pct: float
    target_drop_pct: float


def regulation_advice(
    p_mw: float,
    q_mvar: float,
    r_pu: float,
    x_pu: float,
    current_drop_pct: float,
    target_drop_pct: float,
    tap_step_percent: float = 2.5,
) -> RegulationAdvice:
    """按 ΔU_X 主导的口径反推补偿量与分接步数。

    补偿 Q_c 使 ΔU 从 current 降到 target：
      Q_c ≈ (current-target)/100 · U²/X（pu → Mvar）
    分接步数 = 剩余缺口 / 每步百分比（向上取整由调用方决定）。
    """
    if x_pu <= 0:
        raise ValueError("X=0 时无功补偿对电压损耗无效")
    if target_drop_pct < 0 or current_drop_pct < 0:
        raise ValueError("电压损耗不能为负")
    gap_pct = current_drop_pct - target_drop_pct
    if gap_pct <= 0:
        return RegulationAdvice(
            need_q_mvar=0.0,
            tap_steps=0.0,
            current_drop_pct=current_drop_pct,
            target_drop_pct=target_drop_pct,
        )
    # pu 口径：ΔΔU/100 = Q_c_pu·X/U² → Q_c(pu) = gap/100/X（U≈1）
    q_c_pu = gap_pct / 100 / x_pu
    q_c_mvar = q_c_pu * 100
    tap_steps = 0.0
    if tap_step_percent > 0:
        tap_steps = gap_pct / tap_step_percent
    return RegulationAdvice(
        need_q_mvar=q_c_mvar,
        tap_steps=tap_steps,
        current_drop_pct=current_drop_pct,
        target_drop_pct=target_drop_pct,
    )
