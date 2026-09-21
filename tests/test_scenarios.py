"""M13：场景库。"""
import json
from pathlib import Path

import pytest

from pscalc.scenarios import (
    SCENARIO_DIR,
    ScenarioError,
    list_scenarios,
    load_scenario,
    run_scenario,
)


class TestListScenarios:
    def test_builtin_scenarios_found(self):
        files = list_scenarios()
        assert len(files) >= 3
        names = {f.stem for f in files}
        assert {"substation_110", "windfarm_35", "distribution_10"} <= names

    def test_dir_is_inside_package(self):
        assert SCENARIO_DIR.exists()


class TestLoadScenario:
    def test_substation_110(self):
        net, loads = load_scenario(SCENARIO_DIR / "substation_110.json")
        assert set(net.buses) == {"G", "110bus", "10bus"}
        assert loads["10bus"] == (30.0, 10.0)
        assert net.validate() == []

    def test_windfarm_radial(self):
        net, loads = load_scenario(SCENARIO_DIR / "windfarm_35.json")
        assert set(net.buses) == {"SYS", "BUS35", "WT1", "WT2"}
        assert net.validate() == []
        assert loads["WT1"] == (8.0, 2.5)

    def test_distribution_10(self):
        net, _loads = load_scenario(SCENARIO_DIR / "distribution_10.json")
        assert set(net.buses) == {"SRC", "N1", "N2", "N3"}
        assert net.validate() == []

    def test_ikss_source_flavor(self):
        net, _ = load_scenario(SCENARIO_DIR / "distribution_10.json")
        assert "SRC" in net.buses

    def test_missing_field_raises(self, tmp_path: Path):
        data = {"base": {"s_mva": 100}}
        p = tmp_path / "bad.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ScenarioError):
            load_scenario(p)

    def test_bad_type_raises(self, tmp_path: Path):
        data = {
            "base": {"s_mva": "hundred", "kv": 115},
            "buses": [{"name": "A", "kv": 115}],
        }
        p = tmp_path / "bad2.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ScenarioError):
            load_scenario(p)

    def test_unknown_branch_type(self, tmp_path: Path):
        data = {
            "base": {"s_mva": 100, "kv": 115},
            "buses": [{"name": "A", "kv": 115}, {"name": "B", "kv": 115}],
            "branches": [{"type": "magic", "from": "A", "to": "B"}],
        }
        p = tmp_path / "bad3.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ScenarioError, match="未知支路类型"):
            load_scenario(p)

    def test_loop_topology_rejected(self, tmp_path: Path):
        data = {
            "base": {"s_mva": 100, "kv": 115},
            "buses": [
                {"name": "A", "kv": 115, "source": {"sk_mva": 2000}},
                {"name": "B", "kv": 115},
                {"name": "C", "kv": 115},
            ],
            "branches": [
                {"type": "line", "from": "A", "to": "B", "r": 0.1, "x": 0.4, "km": 1},
                {"type": "line", "from": "B", "to": "C", "r": 0.1, "x": 0.4, "km": 1},
                {"type": "line", "from": "C", "to": "A", "r": 0.1, "x": 0.4, "km": 1},
            ],
        }
        p = tmp_path / "loop.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ScenarioError, match="自检失败"):
            load_scenario(p)


class TestRunScenario:
    @pytest.mark.parametrize("name", ["substation_110", "windfarm_35", "distribution_10"])
    def test_builtin_produces_report(self, name):
        text = run_scenario(SCENARIO_DIR / f"{name}.json")
        assert text.startswith("#")
        assert "短路电流计算" in text
        assert "潮流与电压" in text

    def test_custom_title(self):
        text = run_scenario(
            SCENARIO_DIR / "substation_110.json", title="自定义标题"
        )
        assert text.startswith("# 自定义标题")

    def test_report_numbers_present(self):
        text = run_scenario(SCENARIO_DIR / "substation_110.json")
        # 至少含 3 位小数的电流值
        assert "." in text
