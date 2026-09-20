"""计算书生成（M12）：把计算结果渲染成 Markdown 报告。

  build_report(...)     汇总短路/潮流/校验结果 → 文本
  save_report(...)      写文件（UTF-8）

报告分节：工程概况 → 短路电流表 → 潮流与电压 →
设备校验汇总 → 口径说明（引用的标准条文）。
数字统一保留 2 位小数（电流 3 位）。
"""
from __future__ import annotations

from pathlib import Path

from .equipment import EquipmentCheck
from .network import Network
from .powerflow import PowerFlowResult
from .shortcircuit import ShortCircuitResult


def _fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def build_report(
    title: str,
    net: Network,
    fault_results: dict[str, ShortCircuitResult],
    pf_result: PowerFlowResult | None = None,
    equipment_checks: list[EquipmentCheck] | None = None,
) -> str:
    """生成一份完整计算书的 Markdown 文本。"""
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## 1 工程概况")
    lines.append("")
    lines.append(
        f"- 基准容量：{_fmt(net.base.s_mva, 0)} MVA；"
        f"基准电压：{_fmt(net.base.base_kv, 1)} kV"
    )
    lines.append(f"- 母线数：{len(net.buses)}；支路数：{len(net.branches)}")
    bus_list = "、".join(
        f"{name}({bus.kv:.1f} kV)" for name, bus in net.buses.items()
    )
    lines.append(f"- 母线：{bus_list}")
    lines.append("")

    lines.append("## 2 短路电流计算")
    lines.append("")
    lines.append("IEC 60909 等效电压源法，三相短路。")
    lines.append("")
    lines.append("| 母线 | Un (kV) | c | Ik'' (kA) | ip (kA) | ib (kA) | Ith (kA) | Sk (MVA) | R/X |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for bus in net.buses:
        r = fault_results.get(bus)
        if r is None:
            continue
        rx = r.r_pu / r.x_pu if r.x_pu else float("inf")
        lines.append(
            f"| {r.bus} | {_fmt(r.voltage_kv, 1)} | {_fmt(r.c)} | "
            f"{_fmt(r.ikss_ka, 3)} | {_fmt(r.ip_ka, 3)} | {_fmt(r.ib_ka, 3)} | "
            f"{_fmt(r.ith_ka, 3)} | {_fmt(r.sk_mva)} | {_fmt(rx)} |"
        )
    lines.append("")

    if pf_result is not None:
        lines.append("## 3 潮流与电压")
        lines.append("")
        lines.append("前推回代法，平衡节点电压 1.0 pu。")
        lines.append("")
        lines.append("| 母线 | 电压 (pu) |")
        lines.append("|---|---|")
        for bus in sorted(pf_result.voltages):
            lines.append(f"| {bus} | {_fmt(pf_result.voltages[bus], 4)} |")
        lines.append("")
        lines.append(f"- 网络损耗：{_fmt(pf_result.total_loss_mw)} MW")
        lines.append(f"- 迭代次数：{pf_result.iterations}（收敛：{pf_result.converged}）")
        lines.append("")

    if equipment_checks:
        lines.append("## 4 设备校验汇总")
        lines.append("")
        n_pass = sum(1 for c in equipment_checks if c.ok)
        lines.append(f"- 共 {len(equipment_checks)} 项，通过 {n_pass} 项")
        for c in equipment_checks:
            lines.append(f"- {c.summary()}")
        lines.append("")

    lines.append("## 5 口径说明")
    lines.append("")
    lines.append("- 短路：IEC 60909-0 等效电压源法；峰值系数 κ=1.02+0.98·e^(-3R/X)")
    lines.append("- 热稳定：Ith²·tk 与设备短时耐受电流能力比较（时间修正）")
    lines.append("- 潮流：辐射网前推回代；负荷恒功率")
    lines.append("- 无功补偿：Q=P·(tanφ₁-tanφ₂)")
    return "\n".join(lines) + "\n"


def save_report(text: str, path: str | Path) -> Path:
    """把报告文本写入文件。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p
