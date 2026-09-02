"""标幺值体系（M1）。

短路计算按 IEC 60909 的标幺值（per-unit）口径进行：
把系统阻抗、电压、功率归算到统一的基准容量 S_base 与
基准电压 U_base（平均额定电压，kV）下。

  SystemBase(s_mva, base_kv)   基准容量/电压；派生基准电流、基准阻抗
  pu(z_ohm, base_kv)           有名值阻抗 → 标幺值
  from_pu(z_pu, base_kv)       标幺值 → 有名值（M5 校验用）
  voltage_levels()             常用电压等级的平均额定电压表

电压调整系数 c（IEC 60909 表 I）由 voltage 模块的 c_factor 提供。
"""
from __future__ import annotations

from dataclasses import dataclass

# 常用电压等级的的平均额定电压 Uq（kV）。标幺值归算和 c 系数
# 查表都以这一档为口径；不在表内的等级按有名值处理并给出警告。
AVERAGE_VOLTAGES: dict[str, float] = {
    "0.4": 0.4,
    "3": 3.0,
    "6": 6.0,
    "10": 10.0,
    "35": 37.0,
    "66": 69.0,
    "110": 115.0,
    "220": 231.0,
    "330": 345.0,
    "500": 525.0,
}


@dataclass(frozen=True)
class SystemBase:
    """基准容量（MVA）与基准电压（kV）。

    z_base = U_base² / S_base（Ω）；i_base = S_base / (√3·U_base)（kA）。
    """

    s_mva: float
    base_kv: float

    def __post_init__(self) -> None:
        if self.s_mva <= 0 or self.base_kv <= 0:
            raise ValueError("基准容量与基准电压必须为正数")

    @property
    def z_base_ohm(self) -> float:
        """基准阻抗 Ω = U²/S。"""
        return self.base_kv**2 / self.s_mva

    @property
    def i_base_ka(self) -> float:
        """基准电流 kA = S/(√3·U)。"""
        return self.s_mva / (3**0.5 * self.base_kv)


def pu(z_ohm: float, base: SystemBase) -> float:
    """有名值阻抗（Ω）→ 标幺值。"""
    if base.base_kv <= 0:
        raise ValueError("基准电压必须为正数")
    return z_ohm / base.z_base_ohm


def from_pu(z_pu: float, base: SystemBase) -> float:
    """标幺值 → 有名值阻抗（Ω）。"""
    return z_pu * base.z_base_ohm


def voltage_levels() -> dict[str, float]:
    """返回平均额定电压表（等级字符串 → kV）。"""
    return dict(AVERAGE_VOLTAGES)


def average_voltage(kv: float) -> float:
    """把额定电压（kV）折算到所在等级的平均额定电压。

    10.5 kV → 10.0；115 kV → 115；找不到就近等级时报错——
    调用方必须显式给等级，不能静默外推。
    """
    if kv <= 0:
        raise ValueError("电压必须为正数")
    best_name, best_diff = None, None
    for name, uq in AVERAGE_VOLTAGES.items():
        diff = abs(kv - uq)
        if best_diff is None or diff < best_diff:
            best_name, best_diff = name, diff
    assert best_name is not None and best_diff is not None
    if best_diff / AVERAGE_VOLTAGES[best_name] > 0.2:
        raise ValueError(f"电压 {kv} kV 找不到就近的标准等级")
    return AVERAGE_VOLTAGES[best_name]
