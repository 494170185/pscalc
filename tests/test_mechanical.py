"""M18：导线机械计算。"""
import pytest

from pscalc.mechanical import (
    check_clearance,
    max_sag_span,
    sag,
    support_tension,
)


class TestSag:
    def test_formula(self):
        # w=10, L=200, T=20000：10·40000/160000=2.5
        assert sag(10, 200, 20000) == pytest.approx(2.5)

    def test_longer_span_more_sag(self):
        assert sag(10, 300, 20000) > sag(10, 200, 20000)

    def test_higher_tension_less_sag(self):
        assert sag(10, 200, 30000) < sag(10, 200, 20000)

    def test_bad_inputs_raise(self):
        for args in [(0, 200, 20000), (10, 0, 20000), (10, 200, 0)]:
            with pytest.raises(ValueError):
                sag(*args)


class TestMaxSagSpan:
    def test_roundtrip_with_sag(self):
        span = max_sag_span(10, 20000, 2.5)
        assert sag(10, span, 20000) == pytest.approx(2.5)

    def test_larger_allowed_sag_longer_span(self):
        assert max_sag_span(10, 20000, 4) > max_sag_span(10, 20000, 2)

    def test_zero_allowed_raises(self):
        with pytest.raises(ValueError):
            max_sag_span(10, 20000, 0)


class TestSupportTension:
    def test_zero_vertical_equals_horizontal(self):
        assert support_tension(20000, 10, 0) == pytest.approx(20000)

    def test_vertical_added(self):
        # 垂直分量 10·200/2=1000 → √(20000²+1000²)
        assert support_tension(20000, 10, 200) == pytest.approx(
            (20000**2 + 1000**2) ** 0.5
        )

    def test_negative_span_raises(self):
        with pytest.raises(ValueError):
            support_tension(20000, 10, -1)


class TestCheckClearance:
    def test_pass(self):
        c = check_clearance(sag_m=2.5, attachment_height_m=12, required_clearance_m=6)
        assert c.ok

    def test_fail(self):
        c = check_clearance(sag_m=8.0, attachment_height_m=12, required_clearance_m=6)
        assert not c.ok

    def test_zero_height_raises(self):
        with pytest.raises(ValueError):
            check_clearance(1, 0, 5)
