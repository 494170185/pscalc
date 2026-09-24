"""M25：结果回归对比。"""
from pscalc.regression import (
    FieldDiff,
    diff,
    snapshot_faults,
    snapshot_from_results,
)
from tests.test_shortcircuit import build_net


class TestSnapshot:
    def test_rounded_values(self):
        snap = snapshot_faults(build_net())
        for fields in snap.values():
            for value in fields.values():
                assert value == round(value, 6)

    def test_buses_covered(self):
        snap = snapshot_faults(build_net())
        assert set(snap) == {"G", "A", "B"}

    def test_from_results_matches_snapshot(self):
        net = build_net()
        snap1 = snapshot_faults(net)
        from pscalc.shortcircuit import fault_currents

        snap2 = snapshot_from_results(fault_currents(net))
        assert snap1 == snap2


class TestDiff:
    def test_identical_snapshots_pass(self):
        snap = snapshot_faults(build_net())
        report = diff(snap, dict(snap))
        assert report.ok()
        assert report.diffs == []

    def test_recomputed_identical_pass(self):
        net = build_net()
        base = snapshot_faults(net)
        again = snapshot_faults(build_net())
        report = diff(base, again)
        assert report.ok()

    def test_value_change_detected(self):
        snap = snapshot_faults(build_net())
        changed = {b: dict(v) for b, v in snap.items()}
        changed["B"]["ikss_ka"] = changed["B"]["ikss_ka"] * 1.5
        report = diff(snap, changed)
        assert not report.ok()
        assert any(d.bus == "B" and d.field == "ikss_ka" for d in report.diffs)

    def test_missing_bus_fails(self):
        snap = snapshot_faults(build_net())
        reduced = {b: v for b, v in snap.items() if b != "B"}
        report = diff(snap, reduced)
        assert not report.ok()
        assert report.missing_buses == ["B"]

    def test_added_bus_fails(self):
        snap = snapshot_faults(build_net())
        extended = dict(snap)
        extended["NEW"] = {"ikss_ka": 1.0}
        report = diff(snap, extended)
        assert report.added_buses == ["NEW"]
        assert not report.ok()

    def test_tiny_change_within_tolerance(self):
        snap = snapshot_faults(build_net())
        changed = {b: dict(v) for b, v in snap.items()}
        changed["A"]["ikss_ka"] += 1e-9
        report = diff(snap, changed)
        # 差异被记录但相对变化在容差内
        assert report.ok(tol=1e-4)


class TestReport:
    def test_relative_change_zero_baseline(self):
        d = FieldDiff("X", "ikss_ka", 0.0, 1.0)
        assert d.relative_change() == float("inf")
        d2 = FieldDiff("X", "ikss_ka", 0.0, 0.0)
        assert d2.relative_change() == 0.0

    def test_summary_text(self):
        snap = snapshot_faults(build_net())
        changed = {b: dict(v) for b, v in snap.items()}
        changed["B"]["ip_ka"] *= 2
        report = diff(snap, changed)
        text = report.summary()
        assert "B" in text or "差异" in text
        assert "通过" in diff(snap, dict(snap)).summary()
