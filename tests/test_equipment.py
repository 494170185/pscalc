"""M11：设备校验。"""
import pytest

from pscalc.equipment import (
    BreakerRating,
    BusbarRating,
    CableRating,
    EquipmentCheck,
    OverheadRating,
    check_breaker,
    check_busbar,
    check_cable,
    check_overhead,
)


class TestMargins:
    def test_pass_positive_margin(self):
        ok, m = True, 10.0
        ec = EquipmentCheck("t", ok, m)
        assert "通过" in ec.summary()

    def test_fail_negative_margin(self):
        ec = EquipmentCheck("t", False, -15.0)
        assert "不通过" in ec.summary()


class TestBreaker:
    def test_all_pass(self):
        rating = BreakerRating(
            rated_breaking_ka=31.5, rated_peak_ka=80, rated_thermal_ka=31.5
        )
        checks = check_breaker(
            rating, ikss_ka=20.0, ip_ka=50.0, ith_ka=25.0, tk_s=1.0
        )
        assert len(checks) == 3
        assert all(c.ok for c in checks)

    def test_breaking_fails(self):
        rating = BreakerRating(
            rated_breaking_ka=20.0, rated_peak_ka=50, rated_thermal_ka=20
        )
        checks = check_breaker(
            rating, ikss_ka=25.0, ip_ka=40.0, ith_ka=18.0, tk_s=1.0
        )
        breaking = next(c for c in checks if "开断" in c.item)
        assert not breaking.ok

    def test_peak_fails(self):
        rating = BreakerRating(
            rated_breaking_ka=40.0, rated_peak_ka=50, rated_thermal_ka=40
        )
        checks = check_breaker(
            rating, ikss_ka=20.0, ip_ka=60.0, ith_ka=18.0, tk_s=1.0
        )
        peak = next(c for c in checks if "动稳定" in c.item)
        assert not peak.ok

    def test_thermal_time_scaling(self):
        """热稳定时间修正：需求 tk=2s 时能量比 tk=1s 大 √2 倍。"""
        rating = BreakerRating(
            rated_breaking_ka=40, rated_peak_ka=100, rated_thermal_ka=20,
            thermal_time_s=3.0,
        )
        short = check_breaker(rating, 20, 50, 20, tk_s=1.0)
        long = check_breaker(rating, 20, 50, 20, tk_s=4.0)
        m_short = next(c for c in short if "热稳定" in c.item).margin_pct
        m_long = next(c for c in long if "热稳定" in c.item).margin_pct
        assert m_long < m_short

    def test_bad_tk_raises(self):
        rating = BreakerRating(31.5, 80, 31.5)
        with pytest.raises(ValueError):
            check_breaker(rating, 20, 50, 25, tk_s=0)


class TestBusbar:
    def test_minimum_area_formula(self):
        # Ith=20kA, t=1s, k=171 → S_min ≈ 117 mm²
        rating = BusbarRating(area_mm2=125.0, k_factor=171.0)
        checks = check_busbar(rating, ith_ka=20.0, tk_s=1.0)
        assert checks[0].ok

    def test_undersized_fails(self):
        rating = BusbarRating(area_mm2=100.0, k_factor=171.0)
        checks = check_busbar(rating, ith_ka=25.0, tk_s=2.0)
        assert not checks[0].ok

    def test_longer_time_needs_more(self):
        rating = BusbarRating(area_mm2=125.0, k_factor=171.0)
        t1 = check_busbar(rating, 20.0, tk_s=1.0)[0]
        t2 = check_busbar(rating, 20.0, tk_s=4.0)[0]
        assert t2.margin_pct < t1.margin_pct


class TestCable:
    def test_thermal_only(self):
        rating = CableRating(area_mm2=95.0, k_factor=142.0)
        checks = check_cable(rating, ith_ka=15.0, tk_s=0.5)
        assert len(checks) == 1
        assert checks[0].ok

    def test_with_ampacity(self):
        rating = CableRating(area_mm2=95.0, k_factor=142.0, ampacity_a=240.0)
        checks = check_cable(rating, 15.0, 0.5, load_current_a=200.0)
        assert len(checks) == 2
        assert all(c.ok for c in checks)

    def test_ampacity_overload(self):
        rating = CableRating(area_mm2=95.0, k_factor=142.0, ampacity_a=200.0)
        checks = check_cable(rating, 15.0, 0.5, load_current_a=250.0)
        assert not checks[1].ok

    def test_ampacity_without_current_raises(self):
        rating = CableRating(area_mm2=95.0, k_factor=142.0, ampacity_a=200.0)
        with pytest.raises(ValueError):
            check_cable(rating, 15.0, 0.5, load_current_a=0)


class TestOverhead:
    def test_pass(self):
        rating = OverheadRating(ampacity_a=610.0)
        checks = check_overhead(rating, load_current_a=400.0)
        assert checks[0].ok

    def test_fail(self):
        rating = OverheadRating(ampacity_a=300.0)
        checks = check_overhead(rating, load_current_a=400.0)
        assert not checks[0].ok

    def test_zero_current_raises(self):
        rating = OverheadRating(ampacity_a=300.0)
        with pytest.raises(ValueError):
            check_overhead(rating, load_current_a=0)
