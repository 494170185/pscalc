"""M9：电压损耗与调压。"""
import pytest

from pscalc.elements import LineParams, SourceParams
from pscalc.network import Network
from pscalc.perunit import SystemBase
from pscalc.powerflow import solve
from pscalc.voltagedrop import (
    drop_from_impedance,
    regulation_advice,
    voltage_drop,
)

BASE = SystemBase(s_mva=100.0, base_kv=115.0)


def build_chain() -> Network:
    net = Network(BASE)
    net.add_bus("S", 115.0, is_source=True)
    net.add_bus("A", 115.0)
    net.add_source("S", SourceParams(sk_mva=3000))
    net.add_line("S", "A", LineParams(0.1, 0.4, 25))
    return net


class TestVoltageDrop:
    def test_slack_zero_drop(self):
        net = build_chain()
        res = solve(net, {"A": (20.0, 8.0)}, "S")
        assert voltage_drop(res, "S", "S") == pytest.approx(0.0)

    def test_drop_positive_with_load(self):
        net = build_chain()
        res = solve(net, {"A": (20.0, 8.0)}, "S")
        assert voltage_drop(res, "A", "S") > 0

    def test_drop_increases_with_load(self):
        net = build_chain()
        light = solve(net, {"A": (10.0, 4.0)}, "S")
        heavy = solve(net, {"A": (30.0, 12.0)}, "S")
        assert voltage_drop(heavy, "A", "S") > voltage_drop(light, "A", "S")

    def test_unknown_bus_raises(self):
        net = build_chain()
        res = solve(net, {"A": (20.0, 8.0)}, "S")
        with pytest.raises(KeyError):
            voltage_drop(res, "Z", "S")


class TestDropComponents:
    def test_pure_active(self):
        d = drop_from_impedance(p_mw=10, q_mvar=0, r_pu=0.1, x_pu=0.3)
        assert d.du_r == pytest.approx(0.01)
        assert d.du_x == pytest.approx(0.0)

    def test_pure_reactive(self):
        d = drop_from_impedance(p_mw=0, q_mvar=10, r_pu=0.1, x_pu=0.3)
        assert d.du_r == pytest.approx(0.0)
        assert d.du_x == pytest.approx(0.03)

    def test_total(self):
        d = drop_from_impedance(p_mw=10, q_mvar=10, r_pu=0.1, x_pu=0.3)
        assert d.total() == pytest.approx(0.04)

    def test_voltage_scaling(self):
        """电压升高，同一功率的损耗百分比下降。"""
        d1 = drop_from_impedance(10, 10, 0.1, 0.3, u_pu=1.0)
        d2 = drop_from_impedance(10, 10, 0.1, 0.3, u_pu=1.1)
        assert d2.total() < d1.total()

    def test_bad_voltage_raises(self):
        with pytest.raises(ValueError):
            drop_from_impedance(10, 10, 0.1, 0.3, u_pu=0)


class TestRegulationAdvice:
    def test_no_gap_no_action(self):
        adv = regulation_advice(20, 8, 0.05, 0.3, 4.0, 5.0)
        assert adv.need_q_mvar == 0.0
        assert adv.tap_steps == 0.0

    def test_gap_needs_compensation(self):
        adv = regulation_advice(20, 8, 0.05, 0.3, 8.0, 5.0)
        assert adv.need_q_mvar > 0
        # gap 3% / X 0.3 → Q_c = 0.01/0.3 pu = 10 Mvar
        assert adv.need_q_mvar == pytest.approx(10.0)

    def test_tap_steps(self):
        adv = regulation_advice(20, 8, 0.05, 0.3, 8.0, 5.0, tap_step_percent=1.25)
        assert adv.tap_steps == pytest.approx(2.4)

    def test_zero_x_raises(self):
        with pytest.raises(ValueError):
            regulation_advice(20, 8, 0.05, 0.0, 8.0, 5.0)

    def test_negative_drop_raises(self):
        with pytest.raises(ValueError):
            regulation_advice(20, 8, 0.05, 0.3, -1.0, 5.0)
