"""M17：继电保护整定。"""
import pytest

from pscalc.protection import (
    CTParams,
    check_sensitivity,
    instantaneous_pickup,
    overload_pickup,
    relay_settings,
    sensitivity,
    timed_pickup,
)


class TestCTParams:
    def test_ratio(self):
        ct = CTParams(primary_a=600, secondary_a=5)
        assert ct.ratio() == pytest.approx(120.0)

    def test_bad_ratio_raises(self):
        with pytest.raises(ValueError):
            CTParams(primary_a=5, secondary_a=5)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            CTParams(primary_a=-600)


class TestInstantaneous:
    def test_reliability_times_current(self):
        assert instantaneous_pickup(10.0) == pytest.approx(13.0)

    def test_custom_reliability(self):
        assert instantaneous_pickup(10.0, reliability=1.2) == pytest.approx(12.0)

    def test_zero_current_raises(self):
        with pytest.raises(ValueError):
            instantaneous_pickup(0)


class TestTimedPickup:
    def test_coordination(self):
        assert timed_pickup(13.0) == pytest.approx(14.3)

    def test_with_branch_factor(self):
        assert timed_pickup(13.0, branch_factor=1.5) == pytest.approx(1.1 * 1.5 * 13)

    def test_bad_inputs_raise(self):
        with pytest.raises(ValueError):
            timed_pickup(0)
        with pytest.raises(ValueError):
            timed_pickup(10, branch_factor=0)


class TestOverload:
    def test_formula(self):
        # 1.2·100/0.95
        assert overload_pickup(100.0) == pytest.approx(126.32, rel=1e-3)

    def test_lower_return_factor_higher_pickup(self):
        assert overload_pickup(100, return_factor=0.85) > overload_pickup(100)

    def test_bad_return_factor(self):
        with pytest.raises(ValueError):
            overload_pickup(100, return_factor=0.5)

    def test_zero_load_raises(self):
        with pytest.raises(ValueError):
            overload_pickup(0)


class TestSensitivity:
    def test_ratio(self):
        assert sensitivity(12.0, 6.0) == pytest.approx(2.0)

    def test_check_passes(self):
        c = check_sensitivity(12.0, 6.0, minimum=1.5)
        assert c.ok

    def test_check_fails(self):
        c = check_sensitivity(6.0, 6.0, minimum=1.5)
        assert not c.ok

    def test_zero_pickup_raises(self):
        with pytest.raises(ValueError):
            sensitivity(10, 0)


class TestRelaySettings:
    def test_secondary_side(self):
        # 1200 A 一次 / 120 变比 = 10 A
        assert relay_settings(1200, CTParams(600)) == pytest.approx(10.0)

    def test_roundtrip(self):
        ct = CTParams(600)
        sec = relay_settings(900, ct)
        assert sec * ct.ratio() == pytest.approx(900)
