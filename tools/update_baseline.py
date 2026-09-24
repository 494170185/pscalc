"""重生成数值基线（pscalc/scenarios/baseline.py）。

    python tools/update_baseline.py

改动算法后先在 PR 里解释漂移原因，再重跑本脚本。
"""
from __future__ import annotations

import json
from pathlib import Path

from pscalc.regression import snapshot_from_results
from pscalc.scenarios import load_scenario
from pscalc.shortcircuit import fault_currents

BASELINE_SCENARIOS = ("auxiliary_6", "chain_110")


def build_baseline() -> dict:
    out: dict = {}
    for name in BASELINE_SCENARIOS:
        path = Path("pscalc/scenarios") / f"{name}.json"
        net, _ = load_scenario(path)
        out[name] = snapshot_from_results(fault_currents(net))
    return out


def main() -> int:
    baseline = build_baseline()
    target = Path("pscalc/scenarios/baseline.py")
    header = (
        '"""全部内置场景的数值基线（回归契约）。\n\n'
        "文件由 tools/update_baseline.py 生成；tests/test_baseline.py\n"
        "逐场对比。改算法导致数值漂移时，先解释、再更新本文件。\n"
        '"""\n\n'
    )
    body = "BASELINE = " + json.dumps(baseline, ensure_ascii=False, indent=4)
    body = body.replace("true", "True").replace("false", "False").replace("null", "None")
    target.write_text(header + body + "\n", encoding="utf-8")
    print(f"基线已写入 {target}（{len(baseline)} 个场景）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
