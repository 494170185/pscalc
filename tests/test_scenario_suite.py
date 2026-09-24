"""全部内置场景全量冒烟（M29）：加载→短路→潮流→报告。

任何一个场景坏了立刻暴露，不用等单模块测试。
"""
from pathlib import Path

import pytest

from pscalc.scenarios import SCENARIO_DIR, list_scenarios, run_scenario

ALL_SCENARIOS = [f.stem for f in list_scenarios()]


@pytest.mark.parametrize("name", ALL_SCENARIOS)
def test_scenario_runs(name: str):
    text = run_scenario(SCENARIO_DIR / f"{name}.json")
    assert text.startswith("#")
    assert "短路电流计算" in text


@pytest.mark.parametrize("name", ALL_SCENARIOS)
def test_scenario_converges(name: str):
    from pscalc.powerflow import solve
    from pscalc.scenarios import load_scenario

    net, loads = load_scenario(SCENARIO_DIR / f"{name}.json")
    slack = next(n for n, b in net.buses.items() if b.is_source)
    res = solve(net, loads, slack)
    assert res.converged, f"{name} 潮流不收敛"


def test_scenario_count():
    assert len(ALL_SCENARIOS) >= 11


def test_all_scenario_files_exist():
    for stem in ALL_SCENARIOS:
        assert Path(SCENARIO_DIR / f"{stem}.json").exists()
