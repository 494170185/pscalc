"""M26：CLI check/export 子命令。"""
from pathlib import Path

import pytest

from pscalc.cli import main
from pscalc.scenarios import ScenarioError


class TestCheck:
    def test_builtin_scenario_passes(self, capsys):
        assert main(["check", "substation_110"]) == 0
        out = capsys.readouterr().out
        assert "自检通过" in out
        assert "拓扑自检" in out

    def test_unknown_scenario_raises(self):
        with pytest.raises(ScenarioError):
            main(["check", "no_such"])

    def test_bad_scenario_file(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text("{}", encoding="utf-8")
        with pytest.raises(ScenarioError):
            main(["check", str(bad)])


class TestExport:
    def test_csv_to_stdout(self, capsys):
        assert main(["export", "windfarm_35", "--format", "csv"]) == 0
        out = capsys.readouterr().out
        assert "ikss_ka" in out

    def test_json_to_file(self, tmp_path: Path, capsys):
        target = tmp_path / "faults.json"
        assert main(["export", "chain_110", "--format", "json", "-o", str(target)]) == 0
        import json

        payload = json.loads(target.read_text(encoding="utf-8"))
        assert "STA" in payload

    def test_default_format_is_csv(self, capsys):
        assert main(["export", "auxiliary_6"]) == 0
        out = capsys.readouterr().out
        assert "," in out

    def test_bad_format_rejected(self):
        with pytest.raises(SystemExit):
            main(["export", "chain_110", "--format", "xml"])


class TestHelp:
    def test_check_in_help(self, capsys):
        main([])
        out = capsys.readouterr().out
        assert "check" in out
        assert "export" in out
