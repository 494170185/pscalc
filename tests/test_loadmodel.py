"""M4：负荷建模与曲线。"""
import pytest

from pscalc.loadmodel import (
    Load,
    LoadCurve,
    load_set,
    scale_curve,
    typical_curve,
)


class TestLoad:
    def test_negative_p_raises(self):
        with pytest.raises(ValueError):
            Load(p_mw=-1, q_mvar=0)

    def test_zero_ok(self):
        ld = Load(p_mw=0, q_mvar=0)
        assert ld.p_mw == 0


class TestLoadSet:
    def test_sum(self):
        loads = [Load(10, 5, "a"), Load(20, 8, "b")]
        p, q = load_set(loads)
        assert p == pytest.approx(30)
        assert q == pytest.approx(13)

    def test_coincidence(self):
        loads = [Load(10, 5, "a"), Load(20, 8, "b")]
        p, q = load_set(loads, coincidence=0.9)
        assert p == pytest.approx(27)
        assert q == pytest.approx(11.7)

    def test_bad_coincidence(self):
        with pytest.raises(ValueError):
            load_set([Load(1, 0)], coincidence=0)
        with pytest.raises(ValueError):
            load_set([Load(1, 0)], coincidence=1.5)

    def test_empty(self):
        p, q = load_set([])
        assert p == 0 and q == 0


class TestLoadCurve:
    def test_wrong_length_raises(self):
        with pytest.raises(ValueError):
            LoadCurve((1.0,) * 23)

    def test_negative_raises(self):
        vals = [1.0] * 24
        vals[3] = -0.5
        with pytest.raises(ValueError):
            LoadCurve(tuple(vals))

    def test_peak_and_energy(self):
        vals = [1.0] * 24
        vals[17] = 2.0
        c = LoadCurve(tuple(vals))
        assert c.peak() == 2.0
        assert c.energy_mwh() == pytest.approx(25.0)

    def test_load_factor(self):
        vals = [1.0] * 24
        vals[17] = 2.0
        c = LoadCurve(tuple(vals))
        # 23 个 1.0 + 1 个 2.0：电量 25，平均 25/24，峰值 2 → 25/48
        assert c.load_factor() == pytest.approx(25 / 48)
    def test_value_at_bounds(self):
        c = typical_curve(100)
        assert c.value_at(0) == pytest.approx(62)
        with pytest.raises(ValueError):
            c.value_at(24)


class TestScaleCurve:
    def test_scale(self):
        c = typical_curve(100)
        c2 = scale_curve(c, 200)
        assert c2.peak() == pytest.approx(200)
        assert c2.load_factor() == pytest.approx(c.load_factor())

    def test_scale_zero_curve(self):
        c = LoadCurve(tuple([0.0] * 24))
        c2 = scale_curve(c, 24)
        assert c2.energy_mwh() == pytest.approx(24)

    def test_negative_target_raises(self):
        c = typical_curve(100)
        with pytest.raises(ValueError):
            scale_curve(c, -5)


def test_typical_curve_shape():
    c = typical_curve(50)
    assert c.peak() == pytest.approx(50)
    assert min(c.values) >= 0.5 * 50 * 0.9  # 谷值约为峰值的 54%
    assert 0.75 < c.load_factor() < 0.9
