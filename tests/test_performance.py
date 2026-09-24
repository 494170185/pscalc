"""性能冒烟测试：全场景跑通在秒级。

防退化用：算法改动把短路/潮流拖慢到工程不可用时
（比如前推回代迭代爆炸）立刻报警。
"""
import time

from pscalc.powerflow import solve
from pscalc.regression import snapshot_faults
from pscalc.scenarios import list_scenarios, load_scenario
from pscalc.shortcircuit import fault_currents


def test_all_scenarios_under_5s():
    start = time.perf_counter()
    for f in list_scenarios():
        net, loads = load_scenario(f)
        fault_currents(net)
        slack = next(n for n, b in net.buses.items() if b.is_source)
        solve(net, loads, slack)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"12 个场景跑了 {elapsed:.1f}s"


def test_single_scenario_under_500ms():
    net, _ = load_scenario("pscalc/scenarios/chain_110.json")
    start = time.perf_counter()
    snapshot_faults(net)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5
