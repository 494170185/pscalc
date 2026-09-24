"""示例：短路电流全链路计算。

    python examples/example_shortcircuit.py
"""
from pscalc.elements import LineParams, SourceParams, TransformerParams
from pscalc.network import Network
from pscalc.perunit import SystemBase
from pscalc.shortcircuit import fault_currents


def main() -> None:
    base = SystemBase(s_mva=100.0, base_kv=115.0)
    net = Network(base)
    net.add_bus("G", 115.0, is_source=True)
    net.add_bus("A", 115.0)
    net.add_bus("B", 10.0)
    net.add_source("G", SourceParams(sk_mva=2000))
    net.add_line("G", "A", LineParams(0.1, 0.4, 30))
    net.add_transformer("A", "B", TransformerParams(sn_mva=50, uk_percent=10.5, pk_kw=210))

    for bus, r in fault_currents(net).items():
        print(
            f"{bus:>4} ({r.voltage_kv:>6.1f} kV)  "
            f"Ik''={r.ikss_ka:7.3f} kA  ip={r.ip_ka:7.3f} kA  "
            f"Ith={r.ith_ka:7.3f} kA  Sk={r.sk_mva:8.1f} MVA"
        )

if __name__ == "__main__":
    main()
