"""M22：需侧负荷统计。"""
import math

import pytest

from pscalc.demand import (
    DemandSummary,
    DeviceLoad,
    binomial_method,
    demand_method,
    demand_summary,
    reactive_demand,
)


def sample_devices() -> list[DeviceLoad]:
    return [
        DeviceLoad("motor1", 100, 0.7, 0.8),
        DeviceLoad("motor2", 50, 0.6, 0.85),
        DeviceLoad("heater", 30, 1.0, 1.0),
    ]


class TestDeviceLoad:
    def test_demand(self):
        d = DeviceLoad("m", 100, 0.7, 0.8)
        assert d.demand_kw() == pytest.approx(70.0)

    def test_reactive(self):
        d = DeviceLoad("m", 100, 0.7, 0.8)
        assert d.reactive_kvar() == pytest.approx(70 * math.tan(math.acos(0.8)))

    def test_bad_kd(self):
        with pytest.raises(ValueError):
            DeviceLoad("m", 100, 1.5, 0.8)

    def test_bad_pf(self):
        with pytest.raises(ValueError):
            DeviceLoad("m", 100, 0.7, 0)


class TestDemandMethod:
    def test_empty(self):
        assert demand_method([]) == (0.0, 0.0)

    def test_p_q(self):
        p, q = demand_method(sample_devices())
        assert p == pytest.approx(100 * 0.7 + 50 * 0.6 + 30)
        expect_q = 70 * math.tan(math.acos(0.8)) + 30 * math.tan(
            math.acos(0.85)
        )
        assert q == pytest.approx(expect_q)

    def test_pure_resistive_no_q(self):
        _p, q = demand_method([DeviceLoad("h", 10, 1.0, 1.0)])
        assert q == pytest.approx(0.0)


class TestBinomial:
    def test_formula(self):
        devices = sample_devices()
        # b=0.4, c=0.15, top3：0.4·180 + 0.15·180
        val = binomial_method(devices, b=0.4, c=0.15, top_n=3)
        assert val == pytest.approx(0.4 * 180 + 0.15 * 180)

    def test_top_n_limits(self):
        devices = sample_devices()
        full = binomial_method(devices, 0.4, 0.15, top_n=3)
        one = binomial_method(devices, 0.4, 0.15, top_n=1)
        assert one < full

    def test_empty(self):
        assert binomial_method([], 0.4, 0.15) == 0.0

    def test_bad_coefficient(self):
        with pytest.raises(ValueError):
            binomial_method(sample_devices(), -1, 0.15)

    def test_bad_top_n(self):
        with pytest.raises(ValueError):
            binomial_method(sample_devices(), 0.4, 0.15, top_n=0)


class TestReactiveDemand:
    def test_tan(self):
        assert reactive_demand(100, 0.8) == pytest.approx(100 * math.tan(math.acos(0.8)))

    def test_unity_zero(self):
        assert reactive_demand(100, 1.0) == pytest.approx(0.0)

    def test_bad(self):
        with pytest.raises(ValueError):
            reactive_demand(-5, 0.8)


class TestSummary:
    def test_consistency(self):
        s = demand_summary(sample_devices())
        assert s.s30_kva == pytest.approx(math.hypot(s.p30_kw, s.q30_kvar))
        assert 0 < s.overall_pf <= 1

    def test_single_resistive(self):
        s = demand_summary([DeviceLoad("h", 10, 1.0, 1.0)])
        assert s.overall_pf == pytest.approx(1.0)
        assert isinstance(s, DemandSummary)
