"""元件参数（M2）：线路、变压器、电源、负荷的阻抗标幺值模型。

  line_pu(...)       线路 r0+x0（Ω/km）→ r+x（pu）
  transformer_pu(...) 变压器 uk%→x、负载损耗→r（按自身额定容量折算）
  source_pu(...)     系统等值电源：Ik'' 或 Sk'' → 标幺值内阻抗
  load_pu(...)       恒功率负荷的等值阻抗（M4 使用）

所有折算都落到统一 SystemBase；变压器按变比侧归算。
"""
from __future__ import annotations

from dataclasses import dataclass

from .perunit import SystemBase, pu


@dataclass(frozen=True)
class LineParams:
    """线路电气参数（有名值侧）。"""

    r_ohm_per_km: float
    x_ohm_per_km: float
    length_km: float
    b_us_per_km: float = 0.0  # 电纳（对称充电），潮流用

    def __post_init__(self) -> None:
        if self.length_km < 0:
            raise ValueError("线路长度不能为负")

    @property
    def r_ohm(self) -> float:
        return self.r_ohm_per_km * self.length_km

    @property
    def x_ohm(self) -> float:
        return self.x_ohm_per_km * self.length_km


@dataclass(frozen=True)
class TransformerParams:
    """双绕组变压器参数（铭牌口径）。"""

    sn_mva: float
    uk_percent: float
    pk_kw: float = 0.0
    p0_kw: float = 0.0  # 空载损耗，报告与经济性核算用
    i0_percent: float = 0.0

    def __post_init__(self) -> None:
        if self.sn_mva <= 0 or not 0 < self.uk_percent < 100:
            raise ValueError("变压器容量/阻抗参数非法")


@dataclass(frozen=True)
class SourceParams:
    """系统等值电源：短路容量或起始对称短路电流二选一。"""

    sk_mva: float | None = None
    ikss_ka: float | None = None
    voltage_kv: float = 115.0

    def __post_init__(self) -> None:
        if self.sk_mva is None and self.ikss_ka is None:
            raise ValueError("sk_mva 与 ikss_ka 至少给一个")
        if self.sk_mva is not None and self.ikss_ka is not None:
            raise ValueError("sk_mva 与 ikss_ka 只能给一个")
        if self.sk_mva is not None and self.sk_mva <= 0:
            raise ValueError("短路容量必须为正")
        if self.ikss_ka is not None and self.ikss_ka <= 0:
            raise ValueError("起始对称短路电流必须为正")


def line_pu(params: LineParams, base: SystemBase) -> tuple[float, float]:
    """线路 r+x（pu）。并联电纳不做阻抗折算（潮流里单独处理）。"""
    return pu(params.r_ohm, base), pu(params.x_ohm, base)


def transformer_pu(
    params: TransformerParams, base: SystemBase
) -> tuple[float, float]:
    """变压器 r+x（pu，折到 base 基准）。

    x = uk%/100 · S_base/S_n；r 由负载损耗 P_k 折算：
    r = P_k/(1000·S_n) · S_base/S_n。P_k 未给时 r=0（理想变压器）。
    """
    scale = base.s_mva / params.sn_mva
    x_pu = params.uk_percent / 100 * scale
    if params.pk_kw > 0:
        r_pu = params.pk_kw / (1000 * params.sn_mva) * scale
    else:
        r_pu = 0.0
    return r_pu, x_pu


def source_pu(params: SourceParams, base: SystemBase) -> tuple[float, float]:
    """等值电源内阻抗（pu）。系统侧按 X/R=∞ 处理（纯电抗）。"""
    if params.sk_mva is not None:
        z_pu = base.s_mva / params.sk_mva
    else:
        assert params.ikss_ka is not None
        sk = 3**0.5 * params.ikss_ka * params.voltage_kv
        z_pu = base.s_mva / sk
    return 0.0, z_pu


def source_x_over_r_hint(sk_mva: float) -> float:
    """按短路容量给 X/R 经验值（报告口径说明用，非计算依据）。"""
    if sk_mva >= 1000:
        return 20.0
    if sk_mva >= 100:
        return 10.0
    return 5.0


def load_impedance_pu(
    p_mw: float, q_mvar: float, u_kv: float, base: SystemBase
) -> tuple[float, float]:
    """恒功率负荷的等值阻抗（pu，串联口径）。

    Z = U²/(P-jQ) 取其共轭解出的 r+jx；潮流里作为 PQ 节点
    处理，这里给的是近似等值（首端电压估算用）。
    """
    if p_mw <= 0:
        raise ValueError("负荷有功必须为正")
    s = complex(p_mw, q_mvar)
    # U(kV)²/S(MVA) 直接得 Ω（kV²/MVA ≡ Ω）
    z_ohm = (u_kv**2 / s).conjugate()
    r_ohm, x_ohm = z_ohm.real, z_ohm.imag
    return pu(r_ohm, base), pu(x_ohm, base)
