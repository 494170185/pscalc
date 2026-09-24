"""pscalc.cli.check —— 场景自检子命令。

  pscalc check <scenario>    拓扑与数值自检（不写报告）

检查链：JSON 可加载 → 拓扑自检 → 短路可算 → 潮流收敛。
"""
from __future__ import annotations

from pathlib import Path

from ..network import Network
from ..powerflow import solve
from ..scenarios import ScenarioError, list_scenarios, load_scenario
from ..shortcircuit import fault_currents


def resolve(name: str) -> Path:
    """场景名/路径 → 文件路径。"""
    p = Path(name)
    if p.exists():
        return p
    for f in list_scenarios():
        if f.stem == name:
            return f
    raise ScenarioError(f"找不到场景: {name}")


def run_check(name: str) -> tuple[bool, list[str]]:
    """返回 (全部通过, 检查消息列表)。"""
    messages: list[str] = []

    path = resolve(name)
    messages.append(f"加载 {path.name} ... OK")

    net: Network
    net, loads = load_scenario(path)
    messages.append(f"拓扑自检 ... OK（{len(net.buses)} 母线 / {len(net.branches)} 支路）")

    faults = fault_currents(net)
    ik_max = max(r.ikss_ka for r in faults.values())
    messages.append(f"短路计算 ... OK（最大 Ik'' {ik_max:.3f} kA @ "
                    f"{max(faults, key=lambda b: faults[b].ikss_ka)}）")

    slack = next(n for n, b in net.buses.items() if b.is_source)
    pf = solve(net, loads, slack)
    if not pf.converged:
        messages.append(f"潮流计算 ... 不收敛（{pf.iterations} 轮）")
        return False, messages
    messages.append(
        f"潮流计算 ... OK（{pf.iterations} 轮收敛，网损 {pf.total_loss_mw:.3f} MW）"
    )

    return True, messages
