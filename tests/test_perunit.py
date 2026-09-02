"""M1：标幺值体系与电压调整系数。"""
from pscalc import __version__
from pscalc.perunit import (
    SystemBase,
    average_voltage,
    from_pu,
    pu,
    voltage_levels,
)
from pscalc.voltage import c_factor, kappa


class TestSystemBase:
    def test_z_base_10kv_100mva(self):
        base = SystemBase(s_mva=100.0, base_kv=10.0)
        assert abs(base.z_base_ohm - 1.0) < 1e-9

    def test_i_base_10kv_100mva(self):
        base = SystemBase(s_mva=100.0, base_kv=10.0)
        assert abs(base.i_base_ka - 100 / (3**0.5 * 10)) < 1e-9

    def test_invalid_base_raises(self):
        import pytest

        with pytest.raises(ValueError):
            SystemBase(s_mva=-1, base_kv=10)
        with pytest.raises(ValueError):
            SystemBase(s_mva=100, base_kv=0)

    def test_220kv_z_base(self):
        base = SystemBase(s_mva=1000.0, base_kv=231.0)
        assert abs(base.z_base_ohm - 231.0**2 / 1000.0) < 1e-6


class TestPuRoundtrip:
    def test_pu_then_from_pu(self):
        base = SystemBase(s_mva=100.0, base_kv=37.0)
        assert abs(from_pu(pu(12.0, base), base) - 12.0) < 1e-9

    def test_pu_zero(self):
        base = SystemBase(s_mva=100.0, base_kv=10.0)
        assert pu(0.0, base) == 0.0

    def test_known_value(self):
        # 100 MVA / 37 kV 基准，13.69 Ω → 1.0 pu
        base = SystemBase(s_mva=100.0, base_kv=37.0)
        assert abs(pu(13.69, base) - 1.0) < 0.01


class TestVoltageLevels:
    def test_table_has_common_levels(self):
        levels = voltage_levels()
        for kv in ("10", "35", "110", "220", "500"):
            assert kv in levels

    def test_average_voltage_10_5_to_10(self):
        assert average_voltage(10.5) == 10.0

    def test_average_voltage_115(self):
        assert average_voltage(115.0) == 115.0

    def test_average_voltage_unknown_raises(self):
        import pytest

        with pytest.raises(ValueError):
            average_voltage(7.77)

    def test_average_voltage_negative_raises(self):
        import pytest

        with pytest.raises(ValueError):
            average_voltage(-10)


class TestCFactor:
    def test_low_voltage_max(self):
        assert c_factor(0.4) == 1.05

    def test_medium_max(self):
        assert c_factor(10.0) == 1.05

    def test_110kv_max(self):
        assert c_factor(110.0) == 1.1

    def test_min_purpose(self):
        assert c_factor(10.0, purpose="min") == 1.0

    def test_tolerance_explicit(self):
        assert c_factor(0.4, tolerance=6) == 1.06
        assert c_factor(0.4, tolerance=10) == 1.10

    def test_bad_purpose_raises(self):
        import pytest

        with pytest.raises(ValueError):
            c_factor(10.0, purpose="typical")

    def test_bad_tolerance_raises(self):
        import pytest

        with pytest.raises(ValueError):
            c_factor(10.0, tolerance=7)


class TestKappa:
    def test_zero_r_over_x(self):
        assert abs(kappa(0.0) - 2.0) < 1e-9

    def test_typical_value(self):
        # R/X=0.3：κ≈1.42（1.02+0.98·e^-0.9）
        assert 1.41 < kappa(0.3) < 1.43

    def test_large_r_over_x_converges(self):
        assert kappa(100.0) < 1.03

    def test_negative_raises(self):
        import pytest

        with pytest.raises(ValueError):
            kappa(-0.1)


def test_version_string():
    assert __version__ == "0.1.0"
