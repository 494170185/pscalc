"""M14：CLI。"""
from pathlib import Path

import pytest

from pscalc.cli import main
from pscalc.cli.main import main as main_entry


class TestVersion:
    def test_version_prints(self, capsys):
        assert main(["version"]) == 0
        out = capsys.readouterr().out
        assert out.startswith("pscalc ")
        assert "0.1" in out


class TestScenarios:
    def test_lists_builtin(self, capsys):
        assert main(["scenarios"]) == 0
        out = capsys.readouterr().out
        for name in ("substation_110", "windfarm_35", "distribution_10"):
            assert name in out


class TestRun:
    def test_run_builtin_by_name(self, capsys):
        assert main(["run", "substation_110"]) == 0
        out = capsys.readouterr().out
        assert "短路电流计算" in out

    def test_run_with_output(self, tmp_path: Path, capsys):
        target = tmp_path / "out" / "report.md"
        assert main(["run", "windfarm_35", "-o", str(target)]) == 0
        assert target.exists()
        assert "短路电流" in target.read_text(encoding="utf-8")

    def test_run_with_title(self, capsys):
        assert main(["run", "distribution_10", "--title", "测试标题"]) == 0
        out = capsys.readouterr().out
        assert out.startswith("# 测试标题")

    def test_unknown_scenario_exits(self):
        with pytest.raises(SystemExit):
            main(["run", "no_such_scenario"])

    def test_run_by_path(self, tmp_path: Path, capsys):
        src = Path(__file__).parent.parent / "pscalc" / "scenarios" / "substation_110.json"
        assert main(["run", str(src)]) == 0
        out = capsys.readouterr().out
        assert "短路电流" in out


class TestParser:
    def test_no_command_shows_help(self, capsys):
        assert main([]) == 1
        out = capsys.readouterr().out
        assert "usage" in out

    def test_main_entry_alias(self):
        """pyproject scripts 指向的 main() 可直接调用。"""
        assert main_entry(["version"]) == 0
