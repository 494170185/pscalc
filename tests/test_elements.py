"""M2：元件参数折算。"""
import pytest

from pscalc.elements import (
    LineParams,
    SourceParams,
    TransformerParams,
    line_pu,
    load_impedance_pu,
    source_pu,
    source_x_over_r_hint,
    transformer_pu,
)
from pscalc.perunit import SystemBase

BASE = SystemBase(s_mva=100.0, base_kv=115.0)


class TestLineParams:
    def test_post_init_negative_length(self):
        with pytest.raises(ValueError):
            LineParams(r_ohm_per_km=0.1, x_ohm_per_km=0.4, length_km=-1)

    def test_ohm_totals(self):
        line = LineParams(r_ohm_per_km=0.12, x_ohm_per_km=0.4, length_km=10)
        assert line.r_ohm == pytest.approx(1.2)
        assert line.x_ohm == pytest.approx(4.0)

    def test_line_pu(self):
        line = LineParams(r_ohm_per_km=0.12, x_ohm_per_km=0.4, length_km=10)
        r, x = line_pu(line, BASE)
        # z_base = 115²/100 = 132.25
        assert r == pytest.approx(1.2 / 132.25)
        assert x == pytest.approx(4.0 / 132.25)


class TestTransformer:
    def test_post_init_bad_uk(self):
        with pytest.raises(ValueError):
            TransformerParams(sn_mva=50, uk_percent=0)
        with pytest.raises(ValueError):
            TransformerParams(sn_mva=50, uk_percent=120)

    def test_transformer_x(self):
        # 50 MVA、uk=10.5%：x = 0.105·(100/50) = 0.21
        tr = TransformerParams(sn_mva=50, uk_percent=10.5)
        r, x = transformer_pu(tr, BASE)
        assert x == pytest.approx(0.21)
        assert r == 0.0

    def test_transformer_r_from_pk(self):
        # Pk=210 kW：r = 210/(1000·50)·2 = 0.0084
        tr = TransformerParams(sn_mva=50, uk_percent=10.5, pk_kw=210)
        r, _ = transformer_pu(tr, BASE)
        assert r == pytest.approx(0.0084, rel=1e-3)

    def test_same_base_no_scaling(self):
        tr = TransformerParams(sn_mva=100, uk_percent=10.5)
        _, x = transformer_pu(tr, BASE)
        assert x == pytest.approx(0.105)


class TestSource:
    def test_sk_only(self):
        src = SourceParams(sk_mva=2000)
        _, x = source_pu(src, BASE)
        assert x == pytest.approx(0.05)

    def test_ikss_only(self):
        src = SourceParams(ikss_ka=10, voltage_kv=115)
        sk = 3**0.5 * 10 * 115
        _, x = source_pu(src, BASE)
        assert x == pytest.approx(100 / sk)

    def test_neither_raises(self):
        with pytest.raises(ValueError):
            SourceParams()

    def test_both_raises(self):
        with pytest.raises(ValueError):
            SourceParams(sk_mva=100, ikss_ka=1)

    def test_negative_sk_raises(self):
        with pytest.raises(ValueError):
            SourceParams(sk_mva=-5)


class TestXRHint:
    def test_strong_grid(self):
        assert source_x_over_r_hint(2000) == 20.0

    def test_medium(self):
        assert source_x_over_r_hint(500) == 10.0

    def test_weak(self):
        assert source_x_over_r_hint(20) == 5.0


class TestLoadImpedance:
    def test_pure_active(self):
        # 纯有功负荷：Z_pu = S_base/S = 100/10 = 10
        r, x = load_impedance_pu(10.0, 0.0, 115.0, BASE)
        assert r == pytest.approx(10.0)
        assert abs(x) < 1e-9

    def test_non_positive_p_raises(self):
        with pytest.raises(ValueError):
            load_impedance_pu(0, 5.0, 115.0, BASE)
