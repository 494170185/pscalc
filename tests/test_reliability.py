"""M24：供电可靠性。"""
import pytest

from pscalc.reliability import (
    OutageEvent,
    all_indices,
    asai,
    caidi,
    enr,
    saidi,
    saifi,
)


def sample_events() -> list[OutageEvent]:
    return [
        OutageEvent(customers=100, hours=2.0, avg_load_mw=3.0),
        OutageEvent(customers=200, hours=0.5, avg_load_mw=6.0),
    ]


class TestOutageEvent:
    def test_zero_customers_with_hours_raises(self):
        with pytest.raises(ValueError):
            OutageEvent(customers=0, hours=2.0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            OutageEvent(customers=-1, hours=2.0)


class TestSaifi:
    def test_formula(self):
        # (100+200)/1000
        assert saifi(sample_events(), 1000) == pytest.approx(0.3)

    def test_zero_customers_raises(self):
        with pytest.raises(ValueError):
            saifi(sample_events(), 0)


class TestSaidi:
    def test_formula(self):
        # (100·2 + 200·0.5)/1000 = 0.3
        assert saidi(sample_events(), 1000) == pytest.approx(0.3)

    def test_no_events_zero(self):
        assert saidi([], 1000) == 0.0


class TestCaidi:
    def test_ratio(self):
        events = [OutageEvent(100, 2.0), OutageEvent(100, 4.0)]
        # SAIFI=0.2, SAIDI=0.6 → CAIDI=3
        assert caidi(events, 1000) == pytest.approx(3.0)

    def test_no_events_zero(self):
        assert caidi([], 1000) == 0.0


class TestAsai:
    def test_high_for_minor_outages(self):
        assert asai(sample_events(), 1000) == pytest.approx(1 - 0.3 / 8760)

    def test_perfect_when_no_events(self):
        assert asai([], 1000) == 1.0


class TestEnr:
    def test_sum(self):
        # 3·2 + 6·0.5 = 9
        assert enr(sample_events()) == pytest.approx(9.0)

    def test_no_load_zero(self):
        events = [OutageEvent(100, 2.0, avg_load_mw=0.0)]
        assert enr(events) == 0.0


class TestAllIndices:
    def test_keys_and_consistency(self):
        idx = all_indices(sample_events(), 1000)
        assert set(idx) == {"saifi", "saidi", "caidi", "asai", "enr_mwh"}
        assert idx["caidi"] == pytest.approx(idx["saidi"] / idx["saifi"])
        assert 0 < idx["asai"] <= 1
