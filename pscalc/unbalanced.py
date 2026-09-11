"""不对称短路（M6）：单相接地与两相短路。

对称分量法（IEC 60909 的正/负/零序口径）：

  sequence_impedances(net, bus)   各序戴维南阻抗（pu）
  single_phase_earth_fault(...)   单相接地：Ik1 = 3·c·Un/(√3·|Z1+Z2+Z0|)
  two_phase_fault(...)            两相短路：Ik2 = √3·c·Un/(√3·|Z1+Z2|)

零序阻抗由接地方式决定：变压器 YNd 的零序≈变压器漏抗，
不接地系统 Z0=∞（单相接地电流为零）。本模块显式要求
每个元件给出零序口径，不静默假设。
"""
from __future__ import annotations

from dataclasses import dataclass

from .network import Network


@dataclass(frozen=True)
class SequenceImpedances:
    """故障点的三序戴维南阻抗（pu）。"""

    z1: complex
    z2: complex
    z0: complex | None  # None = 不接地/零序开路

    def is_ungrounded(self) -> bool:
        return self.z0 is None


def sequence_impedances(net: Network, bus: str) -> SequenceImpedances:
    """故障点三序阻抗。

    正序 = Network.bus_impedance（M3 口径）；近似取
    Z2 = Z1（架空网与变压器的主流通用近似）；零序由
    net 上的 zero_sequence 字典显式给出——没有给就当不接地。
    """
    r1, x1 = net.bus_impedance(bus)
    z1 = complex(r1, x1)
    z2 = z1
    z0_raw = getattr(net, "zero_sequence", None)
    if z0_raw and bus in z0_raw:
        z0: complex | None = complex(*z0_raw[bus])
    else:
        z0 = None
    return SequenceImpedances(z1=z1, z2=z2, z0=z0)


def single_phase_earth_fault(
    net: Network, bus: str, c: float
) -> tuple[float, SequenceImpedances]:
    """单相接地短路电流（kA，故障母线电压等级）。

    Ik1 = 3·c·Un/(√3·2·|Z1|+|Z0| 之外的严格口径：
    Ik1 = √3·c·Un / |Z1 + Z2 + Z0| —— 下式按该口径实现，
    Un 取故障母线平均额定电压。
    不接地系统返回 0（容性电流不在本库范围）。
    """
    seq = sequence_impedances(net, bus)
    if seq.z0 is None:
        return 0.0, seq
    z_sum = seq.z1 + seq.z2 + seq.z0
    u_kv = net.buses[bus].kv
    # 标幺值口径：I_pu = 3·c/(|Z1+Z2+Z0|)
    i_pu = 3 * c / abs(z_sum)
    i_base_at_bus = net.base.s_mva / (3**0.5 * u_kv)
    return i_pu * i_base_at_bus, seq


def two_phase_fault(
    net: Network, bus: str, c: float
) -> tuple[float, SequenceImpedances]:
    """两相短路电流（kA）：Ik2 = √3·c/|Z1+Z2|（pu 口径）。"""
    seq = sequence_impedances(net, bus)
    z_sum = seq.z1 + seq.z2
    i_pu = 3**0.5 * c / abs(z_sum)
    u_kv = net.buses[bus].kv
    i_base_at_bus = net.base.s_mva / (3**0.5 * u_kv)
    return i_pu * i_base_at_bus, seq
