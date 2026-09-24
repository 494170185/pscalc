"""版本信息工具测试。"""
from pathlib import Path

from pscalc.versioninfo import banner, changelog_head, version_info


class TestVersionInfo:
    def test_has_pscalc_version(self):
        info = version_info()
        assert info["pscalc"] == "0.1.0"

    def test_python_version_present(self):
        info = version_info()
        assert info["python"].count(".") == 2


class TestChangelogHead:
    def test_reads_latest_section(self):
        head = changelog_head()
        assert head is not None
        assert head.startswith("[0.1.0]")

    def test_missing_file_returns_none(self, tmp_path: Path, monkeypatch):
        import pscalc.versioninfo as vi

        monkeypatch.setattr(vi, "_CHANGELOG", tmp_path / "nope.md")
        assert vi.changelog_head() is None


class TestBanner:
    def test_contains_version(self):
        assert "pscalc 0.1.0" in banner()
        assert "Python" in banner()
