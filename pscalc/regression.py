"""结果回归对比（M25）：基线快照 vs 当前计算。

  snapshot_faults(net)          当前短路结果 → {bus: {field: value}}
  diff(baseline, current, tol) 逐项对比，超容差记差异
  RegressionReport              差异清单与判定

用途：改算法/改参数后跑同一场景，确认数值不漂移——
这是库的「数值契约」。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .network import Network
from .shortcircuit import ShortCircuitResult, fault_currents

_COMPARED_FIELDS = ("ikss_ka", "ip_ka", "ib_ka", "ith_ka", "sk_mva")


def snapshot_faults(net: Network) -> dict[str, dict[str, float]]:
    """当前网络短路快照（数值截到 6 位，避免浮点噪声）。"""
    results = fault_currents(net)
    out: dict[str, dict[str, float]] = {}
    for bus, r in results.items():
        out[bus] = {f: round(getattr(r, f), 6) for f in _COMPARED_FIELDS}
    return out


@dataclass(frozen=True)
class FieldDiff:
    """一处数值差异。"""

    bus: str
    field: str
    baseline: float
    current: float

    def relative_change(self) -> float:
        if self.baseline == 0:
            return float("inf") if self.current != 0 else 0.0
        return abs(self.current - self.baseline) / abs(self.baseline)


@dataclass
class RegressionReport:
    """回归对比报告。"""

    diffs: list[FieldDiff] = field(default_factory=list)
    missing_buses: list[str] = field(default_factory=list)
    added_buses: list[str] = field(default_factory=list)

    def ok(self, tol: float = 1e-4) -> bool:
        if self.missing_buses or self.added_buses:
            return False
        return all(d.relative_change() <= tol for d in self.diffs)

    def summary(self) -> str:
        lines = ["回归对比结果："]
        if self.ok():
            lines.append("  通过（无超容差差异）")
        else:
            lines.append(f"  差异 {len(self.diffs)} 处；"
                         f"缺失母线 {self.missing_buses}；新增 {self.added_buses}")
            for d in self.diffs[:10]:
                lines.append(
                    f"  {d.bus}.{d.field}: {d.baseline} → {d.current}"
                    f"（相对变化 {d.relative_change():.2%}）"
                )
        return "\n".join(lines)


def diff(
    baseline: dict[str, dict[str, float]],
    current: dict[str, dict[str, float]],
) -> RegressionReport:
    """两个快照的差异。数值相同/在浮点噪声内不算差异。"""
    report = RegressionReport()
    for bus in baseline:
        if bus not in current:
            report.missing_buses.append(bus)
    for bus in current:
        if bus not in baseline:
            report.added_buses.append(bus)
    for bus in baseline:
        if bus not in current:
            continue
        for f in _COMPARED_FIELDS:
            if f not in current[bus]:
                continue
            b_val = baseline[bus][f]
            c_val = current[bus][f]
            if b_val != c_val:
                report.diffs.append(FieldDiff(bus, f, b_val, c_val))
    return report


def snapshot_from_results(
    results: dict[str, ShortCircuitResult],
) -> dict[str, dict[str, float]]:
    """已有结果集转快照格式。"""
    out: dict[str, dict[str, float]] = {}
    for bus, r in results.items():
        out[bus] = {f: round(getattr(r, f), 6) for f in _COMPARED_FIELDS}
    return out
