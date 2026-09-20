"""M19：经济截面。"""
import pytest

from pscalc.economic import (
    STANDARD_SECTIONS,
    CostParams,
    annual_cost,
    choose_conductor,
    current_density,
    economic_section,
)


class TestCurrentDensity:
    def test_al_table(self):
        assert current_density("al", 2000) == 1.92
        assert current_density("al", 4000) == 1.73
        assert current_density("al", 6000) == 1.54

    def test_cu_table(self):
        assert current_density("cu", 2000) == 2.50
        assert current_density("cu", 6000) == 2.00

    def test_bad_material(self):
        with pytest.raises(ValueError):
            current_density("fe", 4000)

    def test_bad_hours(self):
        with pytest.raises(ValueError):
            current_density("al", 0)


class TestEconomicSection:
    def test_imax_over_j(self):
        # 200 A、铝、4000h：200/1.73
        assert economic_section(200, "al", 4000) == pytest.approx(200 / 1.73)

    def test_more_hours_smaller_section(self):
        # J 变小 → S 变大：长利用小时 → 更大截面
        assert economic_section(200, "al", 6000) > economic_section(200, "al", 2000)

    def test_zero_current_raises(self):
        with pytest.raises(ValueError):
            economic_section(0, "al", 4000)


class TestAnnualCost:
    def test_investment_grows_with_section(self):
        """投资主导（小电流）：大截面年费用更高。

        小电流下损耗小，年费用主要来自投资项（随截面线性增）。
        """
        params = CostParams(
            investment_per_mm2=200.0,
            loss_price_yuan_per_kwh=0.5,
            resistance_per_mm2_km=31.5,
        )
        assert annual_cost(240, 10, 1, params) > annual_cost(120, 10, 1, params)

    def test_loss_dominated_case(self):
        """大电流下损耗费主导：大截面年费用可能更低。"""
        params = CostParams(
            investment_per_mm2=0.5,
            loss_price_yuan_per_kwh=1.0,
            resistance_per_mm2_km=31.5,
        )
        # 损耗随 1/S 下降：500A 时 300 比 95 便宜（损耗主导）
        c95 = annual_cost(95, 500, 10, params)
        c300 = annual_cost(300, 500, 10, params)
        assert c300 < c95

    def test_bad_inputs_raise(self):
        params = CostParams(2.0, 0.5, 31.5)
        with pytest.raises(ValueError):
            annual_cost(0, 100, 1, params)
        with pytest.raises(ValueError):
            annual_cost(95, 100, -1, params)

    def test_bad_params_raise(self):
        with pytest.raises(ValueError):
            CostParams(0, 0.5, 31.5)


class TestChooseConductor:
    def test_returns_standard_section(self):
        params = CostParams(2.0, 0.5, 31.5)
        s = choose_conductor(200, "al", 4000, 10, params)
        assert s in STANDARD_SECTIONS

    def test_zero_current_raises(self):
        params = CostParams(2.0, 0.5, 31.5)
        with pytest.raises(ValueError):
            choose_conductor(0, "al", 4000, 10, params)

    def test_huge_current_picks_large(self):
        params = CostParams(0.5, 0.6, 31.5)
        s = choose_conductor(2000, "al", 4000, 10, params)
        assert s >= 300
