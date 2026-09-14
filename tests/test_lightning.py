"""M16：防雷保护范围。"""
import pytest

from pscalc.lightning import (
    CLASS_ROLLING_RADIUS,
    MastConfig,
    protective_angle,
    rolling_radius,
    rolling_sphere,
    zone_overlap,
)


class TestRollingRadius:
    def test_class_table(self):
        assert rolling_radius(1) == 30.0
        assert rolling_radius(2) == 45.0
        assert rolling_radius(3) == 60.0

    def test_bad_class(self):
        with pytest.raises(ValueError):
            rolling_radius(4)


class TestMastConfig:
    def test_bad_height(self):
        with pytest.raises(ValueError):
            MastConfig(height_m=0)

    def test_bad_class(self):
        with pytest.raises(ValueError):
            MastConfig(height_m=30, building_class=5)


class TestRollingSphere:
    def test_ground_level(self):
        # 二类、h=30：rx = √(30·(90-30)) = √1800
        mast = MastConfig(height_m=30, building_class=2)
        assert rolling_sphere(mast) == pytest.approx(1800**0.5)

    def test_higher_protected_object_smaller_zone(self):
        mast = MastConfig(height_m=30, building_class=2)
        assert rolling_sphere(mast, 10) < rolling_sphere(mast, 0)

    def test_zero_at_mast_tip(self):
        mast = MastConfig(height_m=30, building_class=2)
        assert rolling_sphere(mast, 30) == pytest.approx(0.0, abs=1e-6)

    def test_mast_taller_than_radius_capped(self):
        """h>R 按 R 口径截断（保守）：h=45 与 h=80 的地面保护半径相同。"""
        short = MastConfig(height_m=45, building_class=2)
        tall = MastConfig(height_m=80, building_class=2)
        assert rolling_sphere(tall) == pytest.approx(rolling_sphere(short))

    def test_out_of_range_height_raises(self):
        mast = MastConfig(height_m=30, building_class=2)
        with pytest.raises(ValueError):
            rolling_sphere(mast, 50)


class TestProtectiveAngle:
    def test_tangent_formula(self):
        import math

        mast = MastConfig(height_m=30)
        assert protective_angle(mast, 45) == pytest.approx(30 * math.tan(math.pi / 4))

    def test_zero_angle(self):
        mast = MastConfig(height_m=30)
        assert protective_angle(mast, 0.001) == pytest.approx(0, abs=1e-3)

    def test_bad_angle_raises(self):
        mast = MastConfig(height_m=30)
        with pytest.raises(ValueError):
            protective_angle(mast, 90)


class TestZoneOverlap:
    def test_close_masts_protect_between(self):
        m1 = MastConfig(height_m=30, building_class=2)
        m2 = MastConfig(height_m=30, building_class=2)
        assert zone_overlap(m1, m2, 20) > 0

    def test_far_masts_no_overlap(self):
        m1 = MastConfig(height_m=30, building_class=2)
        m2 = MastConfig(height_m=30, building_class=2)
        assert zone_overlap(m1, m2, 200) == 0.0

    def test_bad_distance(self):
        m1 = MastConfig(height_m=30, building_class=2)
        with pytest.raises(ValueError):
            zone_overlap(m1, m1, 0)


def test_class_table_immutable_keys():
    assert set(CLASS_ROLLING_RADIUS) == {1, 2, 3}
