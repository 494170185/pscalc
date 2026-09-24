"""内置场景的数值基线回归（M27）。

基线文件 baseline.py 由 tools/update_baseline.py 生成；
本测试逐场逐母线对比，任何漂移（>1e-6）都算失败。
"""
import pytest

from pscalc.regression import diff
from pscalc.scenarios import load_scenario
from pscalc.scenarios.baseline import BASELINE
from pscalc.shortcircuit import fault_currents


@pytest.mark.parametrize("scenario", sorted(BASELINE))
def test_scenario_matches_baseline(scenario: str):
    net, _ = load_scenario(f"pscalc/scenarios/{scenario}.json")
    current = {}
    for bus, r in fault_currents(net).items():
        current[bus] = {
            f: round(getattr(r, f), 6)
            for f in ("ikss_ka", "ip_ka", "ib_ka", "ith_ka", "sk_mva")
        }
    report = diff(BASELINE[scenario], current)
    assert report.ok(tol=1e-6), report.summary()


def test_baseline_scenarios_exist():
    from pathlib import Path

    assert len(BASELINE) >= 2
    for name in BASELINE:
        assert Path(f"pscalc/scenarios/{name}.json").exists()


def test_baseline_fields_complete():
    for buses in BASELINE.values():
        for fields in buses.values():
            assert {"ikss_ka", "ip_ka", "sk_mva"} <= set(fields)
