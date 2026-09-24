"""示例：辐射网潮流与电压分布。

    python examples/example_powerflow.py
"""
from pscalc.elements import LineParams, SourceParams
from pscalc.network import Network
from pscalc.perunit import SystemBase
from pscalc.powerflow import solve


def main() -> None:
    base = SystemBase(s_mva=100.0, base_kv=115.0)
    net = Network(base)
    net.add_bus("S", 115.0, is_source=True)
    net.add_bus("A", 115.0)
    net.add_bus("B", 115.0)
    net.add_source("S", SourceParams(sk_mva=3000))
    line = LineParams(0.1, 0.4, 25)
    net.add_line("S", "A", line)
    net.add_line("A", "B", line)

    res = solve(net, {"A": (20.0, 8.0), "B": (15.0, 5.0)}, "S")
    print(f"迭代 {res.iterations} 轮（收敛: {res.converged}）")
    for bus in sorted(res.voltages):
        print(f"  {bus}: {res.voltages[bus]:.4f} pu")
    print(f"网损: {res.total_loss_mw:.3f} MW")

if __name__ == "__main__":
    main()
