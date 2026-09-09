"""M5：短路电流计算（IEC 60909 口径）。"""
import pytest

from pscalc.elements import LineParams, SourceParams, TransformerParams
from pscalc.network import Network
from pscalc.perunit import SystemBase
from pscalc.shortcircuit import BreakOptions, fault_currents, short_circuit

BASE = SystemBase(s_mva=100.0, base_kv=115.0)


def build_net() -> Network:
    """G(115) --30km线路-- A(115) --50MVA主变-- B(10)。"""
    net = Network(BASE)
    net.add_bus("G", 115.0, is_source=True)
    net.add_bus("A", 115.0)
    net.add_bus("B", 10.0)
    net.add_source("G", SourceParams(sk_mva=2000))
    net.add_line("G", "A", LineParams(0.1, 0.4, 30))
    net.add_transformer("A", "B", TransformerParams(sn_mva=50, uk_percent=10.5, pk_kw=210))
    return net


class TestShortCircuit:
    def test_unknown_bus_raises(self):
        net = build_net()
        with pytest.raises(KeyError):
            short_circuit(net, "NOPE")

    def test_ikss_source_bus(self):
        """电源母线短路：Ik'' = c·Sk/(√3·Un)（2000 MVA 系统）。"""
        net = build_net()
        res = short_circuit(net, "G")
        expect = 1.1 * 2000 / (3**0.5 * 115.0)
        assert res.ikss_ka == pytest.approx(expect, rel=1e-6)

    def test_ikss_low_voltage_bus(self):
        """10 kV 母线短路：阻抗法核对。"""
        net = build_net()
        res = short_circuit(net, "B")
        z_base_115 = 115.0**2 / 100.0
        z = complex(0, 0.05) + complex(0.1, 0.4) * 30 / z_base_115
        z += complex(210 / (1000 * 50) * 2, 0.105 * 2)
        i_pu = 1.05 / abs(z)
        i_base_10 = 100 / (3**0.5 * 10)
        assert res.ikss_ka == pytest.approx(i_pu * i_base_10, rel=1e-6)

    def test_ip_from_kappa(self):
        net = build_net()
        res = short_circuit(net, "B")
        rx = res.r_pu / res.x_pu
        from pscalc.voltage import kappa as kappa_fn

        expect_ip = kappa_fn(rx) * 2**0.5 * res.ikss_ka
        assert res.ip_ka == pytest.approx(expect_ip, rel=1e-9)

    def test_sk_mva(self):
        net = build_net()
        res = short_circuit(net, "G")
        assert res.sk_mva == pytest.approx(1.1 * 2000, rel=1e-6)

    def test_min_purpose_lower(self):
        net = build_net()
        r_max = short_circuit(net, "B", purpose="max")
        r_min = short_circuit(net, "B", purpose="min")
        assert r_min.ikss_ka < r_max.ikss_ka
        assert r_min.c == 1.0

    def test_thermal_with_tau(self):
        net = build_net()
        opts = BreakOptions(tk_s=0.5, tau_s=0.045)
        res = short_circuit(net, "B", opts=opts)
        assert res.ith_ka > res.ikss_ka

    def test_thermal_without_tau(self):
        net = build_net()
        opts = BreakOptions(tk_s=0.5, tau_s=None)
        res = short_circuit(net, "B", opts=opts)
        assert res.ith_ka == pytest.approx(res.ikss_ka)

    def test_bad_tk_raises(self):
        net = build_net()
        opts = BreakOptions(tk_s=0, tau_s=0.05)
        with pytest.raises(ValueError):
            short_circuit(net, "B", opts=opts)

    def test_r_over_x(self):
        net = build_net()
        res = short_circuit(net, "B")
        assert res.r_over_x() == pytest.approx(res.r_pu / res.x_pu)


class TestFaultCurrents:
    def test_all_buses_covered(self):
        net = build_net()
        results = fault_currents(net)
        assert set(results) == {"G", "A", "B"}

    def test_far_fault_smaller_capacity(self):
        """电气距离越远，短路容量越小（跨电压层电流反而升高）。"""
        net = build_net()
        results = fault_currents(net)
        assert results["G"].sk_mva > results["A"].sk_mva > results["B"].sk_mva

    def test_lv_current_highest(self):
        """10 kV 侧电流折算后大于 115 kV 侧（变比效应）。"""
        net = build_net()
        results = fault_currents(net)
        assert results["B"].ikss_ka > results["G"].ikss_ka
