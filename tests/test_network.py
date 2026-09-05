"""M3：网络拓扑与戴维南等值阻抗。"""
import pytest

from pscalc.elements import LineParams, SourceParams, TransformerParams
from pscalc.network import Network, NetworkError
from pscalc.perunit import SystemBase

BASE = SystemBase(s_mva=100.0, base_kv=115.0)


def build_simple_net() -> Network:
    """单电源：G(115kV) --线路-- A(115kV) --主变-- B(10kV)。"""
    net = Network(BASE)
    net.add_bus("G", 115.0, is_source=True)
    net.add_bus("A", 115.0)
    net.add_bus("B", 10.0)
    net.add_source("G", SourceParams(sk_mva=2000))
    net.add_line(
        "G", "A", LineParams(r_ohm_per_km=0.1, x_ohm_per_km=0.4, length_km=20)
    )
    net.add_transformer(
        "A", "B", TransformerParams(sn_mva=50, uk_percent=10.5, pk_kw=210)
    )
    return net


class TestBuild:
    def test_duplicate_bus(self):
        net = Network(BASE)
        net.add_bus("A", 10.0)
        with pytest.raises(NetworkError):
            net.add_bus("A", 10.0)

    def test_unknown_bus_on_line(self):
        net = Network(BASE)
        net.add_bus("A", 10.0)
        with pytest.raises(NetworkError):
            net.add_line(
                "A", "X", LineParams(0.1, 0.4, 1.0)
            )

    def test_duplicate_branch_rejected(self):
        net = Network(BASE)
        net.add_bus("A", 10.0)
        net.add_bus("B", 10.0)
        line = LineParams(0.1, 0.4, 1.0)
        net.add_line("A", "B", line)
        with pytest.raises(NetworkError):
            net.add_line("A", "B", line)

    def test_negative_kv_bus(self):
        net = Network(BASE)
        with pytest.raises(NetworkError):
            net.add_bus("bad", -10)


class TestConnected:
    def test_all_connected(self):
        net = build_simple_net()
        assert net.connected_buses("G") == ["A", "B", "G"]

    def test_unknown_start(self):
        net = build_simple_net()
        with pytest.raises(NetworkError):
            net.connected_buses("Z")

    def test_two_islands(self):
        net = Network(BASE)
        net.add_bus("A", 10.0)
        net.add_bus("B", 10.0)
        net.add_bus("C", 10.0)
        net.add_bus("D", 10.0)
        net.add_line("A", "B", LineParams(0.1, 0.4, 1.0))
        net.add_line("C", "D", LineParams(0.1, 0.4, 1.0))
        assert net.connected_buses("A") == ["A", "B"]
        assert net.connected_buses("C") == ["C", "D"]


class TestBusImpedance:
    def test_source_bus_only_internal(self):
        net = build_simple_net()
        r, x = net.bus_impedance("G")
        # 只有电源内阻抗 0.05
        assert r == pytest.approx(0.0)
        assert x == pytest.approx(0.05)

    def test_through_line_and_transformer(self):
        net = build_simple_net()
        r, x = net.bus_impedance("B")
        # 电源内阻抗 j0.05 + 线路(2+j8 Ω → pu) + 变压器(0.0084+j0.21)
        z_base_115 = 115.0**2 / 100.0
        z = complex(0.0, 0.05) + complex(0.1, 0.4) * 20 / z_base_115
        z += complex(210 / (1000 * 50) * 2, 0.105 * 2)
        assert r == pytest.approx(z.real, rel=1e-6)
        assert x == pytest.approx(z.imag, rel=1e-6)

    def test_disconnected_raises(self):
        net = Network(BASE)
        net.add_bus("G", 115.0, is_source=True)
        net.add_bus("X", 10.0)
        net.add_source("G", SourceParams(sk_mva=2000))
        with pytest.raises(NetworkError):
            net.bus_impedance("X")

    def test_no_source_raises(self):
        net = Network(BASE)
        net.add_bus("A", 10.0)
        with pytest.raises(NetworkError):
            net.bus_impedance("A")

    def test_two_parallel_sources(self):
        """两个电源到同一故障点 → 路径阻抗并联。"""
        net = Network(BASE)
        net.add_bus("G1", 115.0, is_source=True)
        net.add_bus("G2", 115.0, is_source=True)
        net.add_bus("F", 115.0)
        net.add_source("G1", SourceParams(sk_mva=2000))
        net.add_source("G2", SourceParams(sk_mva=2000))
        net.add_line("G1", "F", LineParams(0.1, 0.4, 10))
        net.add_line("G2", "F", LineParams(0.1, 0.4, 10))
        r, x = net.bus_impedance("F")
        # 每条路径 j0.05 + (1+j4)/132.25；两路并联
        z_base = 115.0**2 / 100.0
        z_path = complex(0.0, 0.05) + complex(1.0, 4.0) / z_base
        expect = (z_path * z_path) / (z_path + z_path)
        assert r == pytest.approx(expect.real, rel=1e-6)
        assert x == pytest.approx(expect.imag, rel=1e-6)


class TestValidate:
    def test_valid_network(self):
        net = build_simple_net()
        assert net.validate() == []

    def test_isolated_bus_reported(self):
        net = build_simple_net()
        net.add_bus("lonely", 10.0)
        problems = net.validate()
        assert any("lonely" in p for p in problems)

    def test_no_source_reported(self):
        net = Network(BASE)
        net.add_bus("A", 10.0)
        net.add_bus("B", 10.0)
        net.add_line("A", "B", LineParams(0.1, 0.4, 1.0))
        assert any("没有电源" in p for p in net.validate())

    def test_loop_detected(self):
        net = Network(BASE)
        net.add_bus("A", 10.0)
        net.add_bus("B", 10.0)
        net.add_bus("C", 10.0, is_source=True)
        net.add_source("C", SourceParams(sk_mva=2000))
        net.add_line("A", "B", LineParams(0.1, 0.4, 1.0))
        net.add_line("B", "C", LineParams(0.1, 0.4, 1.0))
        net.add_line("C", "A", LineParams(0.1, 0.4, 1.0))
        assert any("环网" in p for p in net.validate())
