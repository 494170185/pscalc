"""参数库与计算模块的交叉验证（M29）。

catalog 的典型值直接喂给 elements/equipment 的计算函数，
保证「查表 → 计算」链路口径一致。
"""
import pytest

from pscalc.catalog import CABLES, CONDUCTORS, TRANSFORMERS, nearest_capacity
from pscalc.economic import economic_section
from pscalc.elements import TransformerParams, transformer_pu
from pscalc.perunit import SystemBase


class TestTransformerCrossCheck:
    @pytest.mark.parametrize("row", TRANSFORMERS)
    def test_transformer_x_reasonable(self, row: dict):
        base = SystemBase(s_mva=100.0, base_kv=115.0)
        params = TransformerParams(
            sn_mva=row["sn_mva"], uk_percent=row["uk"], pk_kw=row["pk_kw"]
        )
        r, x = transformer_pu(params, base)
        # 100 MVA 基准下 x = uk%·(100/sn)：6.3~240 MVA 全表 0.06~0.75 pu
        assert 0.05 < x < 0.8
        # r/x：小容量配变可达 0.16，大容量低至 0.02
        assert 0 < r / x < 0.2


class TestConductorCrossCheck:
    def test_economic_section_pickable(self):
        """catalog 里总有一档 ≥ 经济截面。"""
        for hours in (2000, 4000, 6000):
            s = economic_section(300, "al", hours)
            row = nearest_capacity("conductors", "area_mm2", s)
            assert row["area_mm2"] >= s

    @pytest.mark.parametrize("row", CONDUCTORS)
    def test_ampacity_monotone_with_area(self, row: dict):
        idx = [c["area_mm2"] for c in CONDUCTORS].index(row["area_mm2"])
        if idx > 0:
            prev = CONDUCTORS[idx - 1]
            assert row["ampacity_a"] > prev["ampacity_a"]


class TestCableCrossCheck:
    @pytest.mark.parametrize("row", CABLES)
    def test_k_factor_matches_equipment(self, row: dict):
        from pscalc.equipment import CableRating

        rating = CableRating(area_mm2=row["area_mm2"], k_factor=row["k"])
        # 热稳定最小截面公式倒推不炸：Ith=20kA、t=0.5s
        s_min = 20e3 * 0.5**0.5 / rating.k_factor
        assert s_min > 0
