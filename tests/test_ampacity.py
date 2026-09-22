"""M21：载流量校正。"""
import pytest

from pscalc.ampacity import (
    ambient_correction,
    derated_ampacity,
    grouping_correction,
    soil_correction,
)


class TestAmbient:
    def test_reference_is_one(self):
        assert ambient_correction(25.0) == pytest.approx(1.0)

    def test_hotter_reduces(self):
        assert ambient_correction(40.0) == pytest.approx(0.87)

    def test_interpolation(self):
        # 22.5°C 介于 20(1.04) 与 25(1.00)：≈1.02
        assert ambient_correction(22.5) == pytest.approx(1.02)

    def test_clamps_below(self):
        assert ambient_correction(5) == pytest.approx(1.11)

    def test_clamps_above(self):
        assert ambient_correction(50) == pytest.approx(0.82)

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            ambient_correction(-5)
        with pytest.raises(ValueError):
            ambient_correction(70)


class TestGrouping:
    def test_single_circuit(self):
        assert grouping_correction(1) == 1.0

    def test_decreases_with_circuits(self):
        assert grouping_correction(3) < grouping_correction(2)

    def test_seven_plus_floor(self):
        assert grouping_correction(8) == 0.72

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            grouping_correction(0)


class TestDerated:
    def test_reference_unchanged(self):
        assert derated_ampacity(400) == pytest.approx(400)

    def test_hot_grouped(self):
        v = derated_ampacity(400, ambient_c=40, circuits=4)
        assert v == pytest.approx(400 * 0.87 * 0.82)

    def test_extra_factor(self):
        assert derated_ampacity(400, extra_factor=0.9) == pytest.approx(360)

    def test_bad_rated_raises(self):
        with pytest.raises(ValueError):
            derated_ampacity(0)

    def test_bad_extra_raises(self):
        with pytest.raises(ValueError):
            derated_ampacity(400, extra_factor=2.0)


class TestSoil:
    def test_reference(self):
        assert soil_correction(1.0) == pytest.approx(1.0)

    def test_dry_soil_reduces(self):
        assert soil_correction(2.0) < soil_correction(1.0)

    def test_wet_soil_slightly_better(self):
        assert soil_correction(0.6) == pytest.approx(1.05)

    def test_very_dry_floor(self):
        assert soil_correction(3.0) == 0.78

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            soil_correction(0)
