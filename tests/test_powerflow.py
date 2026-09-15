"""M8：辐射网前推回代潮流。"""
import pytest

from pscalc.elements import LineParams, SourceParams, TransformerParams
from pscalc.network import Network
from pscalc.perunit import SystemBase
from pscalc.powerflow import solve

BASE = SystemBase(s_mva=100.0, base_kv=115.0)


def build_net() -> Network:
    net = Network(BASE)
    net.add_bus("G", 115.0, is_source=True)
    net.add_bus("A", 115.0)
    net.add_bus("B", 10.0)
    net.add_source("G", SourceParams(sk_mva=2000))
    net.add_line("G", "A", LineParams(0.1, 0.4, 30))
    net.add_transformer("A", "B", TransformerParams(sn_mva=50, uk_percent=10.5, pk_kw=210))
    return net


class TestSolve:
    def test_invalid_topology_raises(self):
        net = Network(BASE)
        net.add_bus("A", 10.0)
        with pytest.raises(ValueError, match="自检"):
            solve(net, {}, "A")

    def test_unknown_slack_raises(self):
        net = build_net()
        with pytest.raises(KeyError):
            solve(net, {}, "NOPE")

    def test_no_load_flat_voltage(self):
        """空载：全网 1.0 pu，零损耗，1 轮收敛。"""
        net = build_net()
        res = solve(net, {}, "G")
        assert all(abs(v - 1.0) < 1e-9 for v in res.voltages.values())
        assert res.total_loss_mw == pytest.approx(0.0, abs=1e-9)
        assert res.converged

    def test_voltage_drop_with_load(self):
        """有载：电压沿供电方向下降。"""
        net = build_net()
        res = solve(net, {"B": (30.0, 10.0)}, "G")
        assert res.voltages["G"] == pytest.approx(1.0)
        assert res.voltages["A"] < 1.0
        assert res.voltages["B"] < res.voltages["A"]

    def test_loss_positive_with_load(self):
        net = build_net()
        res = solve(net, {"B": (30.0, 10.0)}, "G")
        assert res.total_loss_mw > 0

    def test_convergence_flag(self):
        net = build_net()
        res = solve(net, {"B": (30.0, 10.0)}, "G")
        assert res.converged
        assert res.iterations <= 100

    def test_min_voltage_bus(self):
        net = build_net()
        res = solve(net, {"B": (30.0, 10.0)}, "G")
        name, val = res.min_voltage_bus()
        assert name == "B"
        assert val == pytest.approx(res.voltages["B"])

    def test_branch_flow_conservation(self):
        """首端功率 ≥ 末端功率 ≥ 0（辐射网单方向）。"""
        net = build_net()
        res = solve(net, {"B": (30.0, 10.0)}, "G")
        for fl in res.branch_flows:
            assert fl.p_from_mw >= fl.p_to_mw
            assert fl.loss_mw() >= 0

    def test_losses_equal_branch_sum(self):
        net = build_net()
        res = solve(net, {"B": (30.0, 10.0)}, "G")
        branch_sum = sum(fl.loss_mw() for fl in res.branch_flows)
        assert res.total_loss_mw == pytest.approx(branch_sum, rel=1e-6)

    def test_lighter_load_higher_voltage(self):
        """负荷越轻，末端电压越高（单调性）。"""
        net = build_net()
        heavy = solve(net, {"B": (30.0, 10.0)}, "G")
        light = solve(net, {"B": (10.0, 3.0)}, "G")
        assert light.voltages["B"] > heavy.voltages["B"]


class TestTwoLevelNetwork:
    def test_multi_bus_chain(self):
        """四母线链式网络：A-B-C-D，负荷挂 C/D。"""
        net = Network(BASE)
        net.add_bus("S", 115.0, is_source=True)
        net.add_bus("A", 115.0)
        net.add_bus("B", 115.0)
        net.add_bus("C", 115.0)
        net.add_source("S", SourceParams(sk_mva=3000))
        line = LineParams(0.1, 0.4, 10)
        net.add_line("S", "A", line)
        net.add_line("A", "B", line)
        net.add_line("B", "C", line)
        res = solve(net, {"B": (20.0, 5.0), "C": (10.0, 3.0)}, "S")
        assert res.voltages["S"] == pytest.approx(1.0)
        assert res.voltages["A"] > res.voltages["B"] > res.voltages["C"]
        assert res.converged
