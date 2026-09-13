"""阻抗校正（M7）：IEC 60909 的 KT 与 KG。

等效电压源法要求把电源内阻抗按运行状态校正：
  KT（变压器校正，式 12a）：分接不在主抽头/额定电压与
      系统电压不一致时，对变压器阻抗乘 (t_f/t_r)²；
  KG（发电机校正，式 18）：用次暂态电抗折算到 c 口径
      KG = Un/(√3·I_rG·c_max)·(x''d·cosφ/cosφ_rG...) 的工程化
      简化：Z_G,corr = 0.95·x''d（欠励运行保守口径）。

本模块只做「系数计算」，应用由调用方把系数乘进 Branch。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TapCorrection:
    """变压器分接校正参数。"""

    t_f: float  # 实际分接比（运行）
    t_r: float  # 额定分接比（铭牌）

    def __post_init__(self) -> None:
        if self.t_r <= 0 or self.t_f <= 0:
            raise ValueError("分接比必须为正")

    def kt(self) -> float:
        """KT = (t_f/t_r)²。"""
        return (self.t_f / self.t_r) ** 2


@dataclass(frozen=True)
class GeneratorCorrection:
    """发电机校正参数（IEC 60909 §3.6 简化口径）。"""

    xdp_pu: float  # 次暂态电抗（pu，发电机额定基准）
    sn_mva: float  # 发电机额定容量
    sn_base_mva: float  # 系统基准容量

    def __post_init__(self) -> None:
        if self.xdp_pu <= 0 or self.sn_mva <= 0 or self.sn_base_mva <= 0:
            raise ValueError("发电机参数必须为正")

    def kg(self, factor: float = 0.95) -> float:
        """校正后的发电机阻抗（pu，系统基准）。

        Z_G,corr = factor·x''d·S_base/S_n；factor=0.95 为
        IEC 欠励运行保守口径。
        """
        if not 0.5 <= factor <= 1.5:
            raise ValueError("校正系数超出合理范围")
        return factor * self.xdp_pu * self.sn_base_mva / self.sn_mva


def apply_kt(z_pu: float, tap: TapCorrection) -> float:
    """把 KT 应用到变压器电抗（pu）。"""
    return z_pu * tap.kt()


def corrected_generator_x(gen: GeneratorCorrection, factor: float = 0.95) -> float:
    """校正后的发电机次暂态电抗（pu，系统基准）。"""
    return gen.kg(factor)
