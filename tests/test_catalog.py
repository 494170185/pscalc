"""M20：设备参数库。"""
import pytest

from pscalc.catalog import (
    BREAKERS,
    CABLES,
    CONDUCTORS,
    TABLES,
    TRANSFORMERS,
    breaker_by_voltage,
    lookup,
    nearest_capacity,
)


class TestLookup:
    def test_no_filter_returns_all(self):
        assert len(lookup("breakers")) == len(BREAKERS)

    def test_filter_kv(self):
        rows = lookup("breakers", kv=126)
        assert len(rows) == 1
        assert rows[0]["model"] == "LW36"

    def test_filter_model(self):
        rows = lookup("conductors", model="LGJ-240")
        assert rows[0]["ampacity_a"] == 610

    def test_no_match_empty(self):
        assert lookup("transformers", sn_mva=999) == []

    def test_unknown_table_raises(self):
        with pytest.raises(ValueError):
            lookup("nope")


class TestNearestCapacity:
    def test_rounds_up(self):
        row = nearest_capacity("transformers", "sn_mva", 45)
        assert row["sn_mva"] == 50

    def test_exact(self):
        row = nearest_capacity("cables", "area_mm2", 240)
        assert row["model"] == "YJV-3x240"

    def test_no_eligible_raises(self):
        with pytest.raises(ValueError):
            nearest_capacity("conductors", "ampacity_a", 99999)

    def test_unknown_field_raises(self):
        with pytest.raises(ValueError):
            nearest_capacity("cables", "color", 1)

    def test_conductor_for_current(self):
        row = nearest_capacity("conductors", "ampacity_a", 550)
        assert row["model"] == "LGJ-240"


class TestBreakerByVoltage:
    def test_10kv(self):
        rows = breaker_by_voltage(10)
        assert rows[0]["kv"] == 12

    def test_110kv(self):
        rows = breaker_by_voltage(110)
        assert all(r["kv"] >= 110 for r in rows)
        assert rows[0]["model"] == "LW36"

    def test_at_500kv_top_of_table(self):
        rows = breaker_by_voltage(550)
        assert len(rows) == 1
        assert rows[0]["model"] == "LW13"


class TestDataIntegrity:
    def test_all_tables_present(self):
        for name in ("breakers", "transformers", "conductors", "cables"):
            assert name in TABLES
            assert len(TABLES[name]) >= 5

    def test_conductors_sorted_by_area(self):
        areas = [c["area_mm2"] for c in CONDUCTORS]
        assert areas == sorted(areas)

    def test_transformer_uk_in_range(self):
        for t in TRANSFORMERS:
            assert 0 < t["uk"] < 30

    def test_breaker_fields_complete(self):
        for b in BREAKERS:
            for key in ("model", "kv", "breaking_ka", "peak_ka", "thermal_ka"):
                assert key in b

    def test_cable_k_uniform(self):
        assert all(c["k"] == 142 for c in CABLES)
