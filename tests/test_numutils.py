"""M29：数值工具。"""
import pytest

from pscalc.numutils import clamp, format_kv, round_sig, safe_divide


class TestClamp:
    def test_inside_unchanged(self):
        assert clamp(5, 0, 10) == 5

    def test_below_clamped(self):
        assert clamp(-1, 0, 10) == 0

    def test_above_clamped(self):
        assert clamp(11, 0, 10) == 10

    def test_reversed_bounds_raise(self):
        with pytest.raises(ValueError):
            clamp(5, 10, 0)


class TestSafeDivide:
    def test_normal(self):
        assert safe_divide(10, 2) == 5

    def test_zero_fallback(self):
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, fallback=-1) == -1


class TestRoundSig:
    def test_three_digits(self):
        assert round_sig(12345.678) == 12300.0

    def test_small_number(self):
        assert round_sig(0.001234) == 0.00123

    def test_zero(self):
        assert round_sig(0.0) == 0.0

    def test_negative(self):
        assert round_sig(-9876.5) == -9880.0

    def test_bad_digits(self):
        with pytest.raises(ValueError):
            round_sig(1.0, 0)


class TestFormatKv:
    def test_with_unit(self):
        out = format_kv(115.0, "kV")
        assert out.endswith("kV")

    def test_trailing_zeros_stripped(self):
        assert format_kv(10.0, "kA").startswith("10 ")

    def test_three_sig_digits(self):
        assert "16.4" in format_kv(16.364, "kA")
