"""短路电流计算（M5）：IEC 60909 口径的全链路。

  short_circuit(net, fault_bus, ...)  一处短路的完整结果：
      ikss_ka   起始对称短路电流（三相，c·Un/√3/Z₁）
      ip_ka     峰值电流 κ·√2·Ik''
      ib_ka     对称开断电流（延迟切除，无交流衰减时 =Ik''）
      ith_ka    热稳定等效电流（含直流分量）
      sk_mva    短路容量 √3·Un·Ik''

  fault_currents(net, buses)  批量：全部母线逐一短路

直流分量按 IEC 60909 简化口径：直流时间常数取 45 ms
（发电机近区）或 15 ms（系统侧），τ 由调用方显式给。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .network import Network
from .voltage import c_factor, kappa


@dataclass(frozen=True)
class ShortCircuitResult:
    """一处故障的全部短路特征值。"""

    bus: str
    voltage_kv: float
    c: float
    r_pu: float
    x_pu: float
    ikss_ka: float
    ip_ka: float
    ib_ka: float
    ith_ka: float
    sk_mva: float

    def r_over_x(self) -> float:
        """故障点等效 R/X（κ 已按此算过，报告里复述用）。"""
        if self.x_pu == 0:
            raise ValueError("纯阻性故障点，R/X 无意义")
        return self.r_pu / self.x_pu


@dataclass(frozen=True)
class BreakOptions:
    """开断/热稳定参数。

    tk_s       切除时间（s），热稳定积分上限
    tau_s      直流分量时间常数（s）；None = 纯交流（ith=ikss）
    delayed    True 时 ib 按交流无衰减处理（保守口径 = ikss）
    """

    tk_s: float = 0.5
    tau_s: float | None = None
    delayed: bool = True


def _thermal_factor(ikss: float, tk: float, tau: float | None) -> float:
    """热等效系数平方 (Ith/Ik'')² = 1 + m·n（IEC 60909 式 26 简化）。

    m（直流分量）= (2·τ/Tk)·(1-e^(-Tk/τ))；n（交流衰减）这里
    取 1（系统侧馈入，交流分量不衰减的保守场景）。
    """
    if tau is None:
        return 1.0
    if tk <= 0:
        raise ValueError("切除时间必须为正")
    m = (2 * tau / tk) * (1 - math.exp(-tk / tau))
    return 1 + m * 1.0


def short_circuit(
    net: Network, fault_bus: str, purpose: str = "max", opts: BreakOptions | None = None
) -> ShortCircuitResult:
    """三相短路（IEC 60909 等效电压源法）。

    等效电压源 c·Un/√3 加在故障点，网络其余电源置零
    （Network.bus_impedance 已是该口径的戴维南阻抗）。
    """
    if fault_bus not in net.buses:
        raise KeyError(f"母线 {fault_bus} 不存在")
    bus = net.buses[fault_bus]
    opts = opts or BreakOptions()

    r_pu, x_pu = net.bus_impedance(fault_bus)
    z_pu = complex(r_pu, x_pu)
    c = c_factor(bus.kv, purpose=purpose)
    # 标幺值下：I_pu = c·U_base/(√3·|Z|·U_base) ... 直接用 pu 口径
    z_mag = abs(z_pu)
    if z_mag == 0:
        raise ValueError("故障点等效阻抗为零")
    # 标幺值下 I_pu = c/|Z|（√3 已被基准折算吸收）
    i_pu = c / z_mag
    # 电流标幺值在各电压等级同值；实际电流按故障母线电压折算
    i_base_at_bus = net.base.s_mva / (3**0.5 * bus.kv)
    ikss = i_pu * i_base_at_bus

    rx = r_pu / x_pu if x_pu != 0 else 10.0
    k = kappa(rx) if x_pu != 0 else 1.0
    ip = k * 2**0.5 * ikss

    # 交流分量不衰减的保守口径：ib = ikss（delayed 参数为将来
    # 的交流衰减模型预留，当前两分支结果一致，显式记录口径）
    ib = ikss
    thermal_sq = _thermal_factor(ikss, opts.tk_s, opts.tau_s)
    ith = ikss * thermal_sq**0.5

    sk = 3**0.5 * bus.kv * ikss
    return ShortCircuitResult(
        bus=fault_bus,
        voltage_kv=bus.kv,
        c=c,
        r_pu=r_pu,
        x_pu=x_pu,
        ikss_ka=ikss,
        ip_ka=ip,
        ib_ka=ib,
        ith_ka=ith,
        sk_mva=sk,
    )


def fault_currents(
    net: Network, purpose: str = "max", opts: BreakOptions | None = None
) -> dict[str, ShortCircuitResult]:
    """全部母线逐一短路。返回 {母线名: 结果}。"""
    out: dict[str, ShortCircuitResult] = {}
    for name in net.buses:
        out[name] = short_circuit(net, name, purpose=purpose, opts=opts)
    return out
