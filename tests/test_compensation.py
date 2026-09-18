"""M10：无功补偿。"""
import math

import pytest

from pscalc.compensation import (
    auto_config,
    cap_bank_size,
    compensate_effect,
)


class TestCapBankSize:
    def test_pf_08_to_09(self):
        # P=10 MW：tan(acos .8)=0.75, tan(acos .9)=0.4843
        q = cap_bank_size(10.0, 0.8, 0.9)
        expect = 10000 * (math.tan(math.acos(0.8)) - math.tan(math.acos(0.9)))
        assert q == pytest.approx(expect)

    def test_already_at_target_zero(self):
        assert cap_bank_size(10.0, 0.9, 0.9) == pytest.approx(0.0)

    def test_higher_target_more_q(self):
        q1 = cap_bank_size(10.0, 0.8, 0.9)
        q2 = cap_bank_size(10.0, 0.8, 0.95)
        assert q2 > q1

    def test_power_scales_linearly(self):
        assert cap_bank_size(20.0, 0.8, 0.9) == pytest.approx(
            2 * cap_bank_size(10.0, 0.8, 0.9)
        )

    def test_bad_pf_raises(self):
        with pytest.raises(ValueError):
            cap_bank_size(10, 1.2, 0.9)
        with pytest.raises(ValueError):
            cap_bank_size(10, 0.8, 0.0)

    def test_target_below_current_raises(self):
        with pytest.raises(ValueError):
            cap_bank_size(10, 0.9, 0.8)


class TestAutoConfig:
    def test_rounds_up(self):
        cfg = auto_config(1050, 200)
        assert cfg.units == 6
        assert cfg.total_kvar() == 1200

    def test_exact_fit(self):
        cfg = auto_config(1000, 200)
        assert cfg.units == 5

    def test_cap_at_max(self):
        cfg = auto_config(5000, 200, max_units=12)
        assert cfg.units == 12

    def test_negative_q_raises(self):
        with pytest.raises(ValueError):
            auto_config(-5, 200)

    def test_zero_unit_raises(self):
        with pytest.raises(ValueError):
            auto_config(100, 0)


class TestCompensateEffect:
    def test_partial_compensation(self):
        eff = compensate_effect(10.0, 7.5, 3.0)
        # Q_after=4.5 → pf=10/hypot(10,4.5)
        assert eff.pf_after == pytest.approx(10 / math.hypot(10, 4.5))
        assert not eff.over_compensated

    def test_full_compensation(self):
        eff = compensate_effect(10.0, 7.5, 7.5)
        assert eff.pf_after == pytest.approx(1.0)
        assert eff.q_after_mvar == pytest.approx(0.0)

    def test_over_compensation_flag(self):
        eff = compensate_effect(10.0, 3.0, 5.0)
        assert eff.over_compensated
        assert eff.q_after_mvar < 0
        assert eff.q_after_sign_hint() == "超前（进相）"

    def test_improves_pf(self):
        before = 10 / math.hypot(10, 7.5)
        eff = compensate_effect(10.0, 7.5, 3.0)
        assert eff.pf_after > before

    def test_zero_p_raises(self):
        with pytest.raises(ValueError):
            compensate_effect(0, 5, 1)

    def test_degenerate_s_raises(self):
        # P=5、Q=5、补偿 5 → Q_after=0 → pf=1
        eff = compensate_effect(5.0, 5.0, 5.0)
        assert eff.pf_after == pytest.approx(1.0)
        assert eff.q_after_mvar == pytest.approx(0.0)
