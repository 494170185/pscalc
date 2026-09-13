"""M7：变压器分接与发电机阻抗校正。"""
import pytest

from pscalc.correction import (
    GeneratorCorrection,
    TapCorrection,
    apply_kt,
    corrected_generator_x,
)


class TestTapCorrection:
    def test_kt_square_ratio(self):
        tap = TapCorrection(t_f=1.05, t_r=1.0)
        assert tap.kt() == pytest.approx(1.1025)

    def test_kt_identity(self):
        tap = TapCorrection(t_f=1.0, t_r=1.0)
        assert tap.kt() == 1.0

    def test_apply_kt(self):
        tap = TapCorrection(t_f=1.05, t_r=1.0)
        assert apply_kt(0.105, tap) == pytest.approx(0.105 * 1.1025)

    def test_zero_ratio_raises(self):
        with pytest.raises(ValueError):
            TapCorrection(t_f=0, t_r=1.0)

    def test_negative_ratio_raises(self):
        with pytest.raises(ValueError):
            TapCorrection(t_f=-1.0, t_r=1.0)


class TestGeneratorCorrection:
    def test_kg_default_factor(self):
        gen = GeneratorCorrection(xdp_pu=0.2, sn_mva=300, sn_base_mva=100)
        # 0.95·0.2·(100/300)
        assert gen.kg() == pytest.approx(0.95 * 0.2 / 3)

    def test_kg_custom_factor(self):
        gen = GeneratorCorrection(xdp_pu=0.2, sn_mva=100, sn_base_mva=100)
        assert gen.kg(factor=1.0) == pytest.approx(0.2)

    def test_base_scaling(self):
        """基准容量翻倍，校正阻抗翻倍。"""
        g1 = GeneratorCorrection(xdp_pu=0.2, sn_mva=300, sn_base_mva=100)
        g2 = GeneratorCorrection(xdp_pu=0.2, sn_mva=300, sn_base_mva=200)
        assert g2.kg() == pytest.approx(2 * g1.kg())

    def test_bad_factor_raises(self):
        gen = GeneratorCorrection(xdp_pu=0.2, sn_mva=300, sn_base_mva=100)
        with pytest.raises(ValueError):
            gen.kg(factor=0.1)

    def test_negative_xdp_raises(self):
        with pytest.raises(ValueError):
            GeneratorCorrection(xdp_pu=-0.2, sn_mva=300, sn_base_mva=100)

    def test_corrected_generator_x_alias(self):
        gen = GeneratorCorrection(xdp_pu=0.25, sn_mva=200, sn_base_mva=100)
        assert corrected_generator_x(gen) == pytest.approx(gen.kg())
