"""M15：接地网。"""
import pytest

from pscalc.grounding import (
    GridParams,
    allowable_step,
    allowable_touch,
    check_grounding,
    gpr,
    grid_resistance,
)


class TestGridResistance:
    def test_two_term_formula(self):
        # A=100×100=1e4 m², L=2000 m, ρ=100：r=56.4，R=100/225.7+100/2000
        grid = GridParams(area_m2=1e4, total_length_m=2000)
        rg = grid_resistance(100.0, grid)
        import math

        r = math.sqrt(1e4 / math.pi)
        assert rg == pytest.approx(100 / (4 * r) + 100 / 2000)

    def test_lower_rho_lower_rg(self):
        grid = GridParams(area_m2=1e4, total_length_m=2000)
        assert grid_resistance(50, grid) < grid_resistance(100, grid)

    def test_more_mesh_lower_rg(self):
        g1 = GridParams(area_m2=1e4, total_length_m=1000)
        g2 = GridParams(area_m2=1e4, total_length_m=4000)
        assert grid_resistance(100, g2) < grid_resistance(100, g1)

    def test_bad_params_raise(self):
        with pytest.raises(ValueError):
            GridParams(area_m2=0, total_length_m=100)
        with pytest.raises(ValueError):
            grid_resistance(-1, GridParams(1e4, 1000))


class TestAllowables:
    def test_touch_50kg(self):
        # ρs=100, t=0.5：(116+17.4)/√0.5
        assert allowable_touch(100, 0.5) == pytest.approx((116 + 17.4) / 0.5**0.5)

    def test_step_50kg(self):
        assert allowable_step(100, 0.5) == pytest.approx((116 + 69.6) / 0.5**0.5)

    def test_70kg_more_tolerant(self):
        assert allowable_touch(100, 0.5, "70kg") > allowable_touch(100, 0.5, "50kg")

    def test_shorter_time_higher_allowance(self):
        assert allowable_touch(100, 0.2) > allowable_touch(100, 1.0)

    def test_bad_args_raise(self):
        with pytest.raises(ValueError):
            allowable_touch(100, 0)
        with pytest.raises(ValueError):
            allowable_step(-1, 0.5)


class TestGpr:
    def test_product(self):
        assert gpr(1000, 0.5) == pytest.approx(500)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            gpr(-1, 0.5)


class TestCheckGrounding:
    def test_all_pass(self):
        # 接触允许值 188.7V > 估计 150V；Rg 0.48 < 1.0
        grid = GridParams(area_m2=1e4, total_length_m=3000)
        checks = check_grounding(
            rho_ohm_m=100, grid=grid, ig_a=1000,
            est_touch_v=150, est_step_v=250,
            rho_s=100, t_s=0.5, target_rg_ohm=1.0,
        )
        assert len(checks) == 3
        assert all(c.ok for c in checks)

    def test_high_touch_fails(self):
        grid = GridParams(area_m2=1e4, total_length_m=3000)
        checks = check_grounding(
            rho_ohm_m=100, grid=grid, ig_a=1000,
            est_touch_v=2000, est_step_v=300,
            rho_s=100, t_s=0.5,
        )
        assert not checks[0].ok

    def test_without_rg_target(self):
        grid = GridParams(area_m2=1e4, total_length_m=3000)
        checks = check_grounding(
            rho_ohm_m=100, grid=grid, ig_a=1000,
            est_touch_v=200, est_step_v=300,
            rho_s=100, t_s=0.5,
        )
        assert len(checks) == 2
