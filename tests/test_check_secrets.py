"""tools.check_secrets 的测试。

样例密钥都用「拼接生成」写法，避免测试文件本身被扫描器
命中（这是扫描器自己的仓库，CI 会扫全库）。
"""
from pathlib import Path

from tools.check_secrets import main, scan

_AWS = "AKIA" + "IOSFODNN7EXAMPLE"
_PAT = "ghp_" + "16C7e42F292c6912E7710c838347Ae178B4a"
_PW = "p" + "assword123"


class TestScan:
    def test_clean_repo(self):
        findings = scan(Path("."))
        assert findings == []

    def test_detects_aws_key(self, tmp_path: Path):
        bad = tmp_path / "cfg.txt"
        bad.write_text(f"key = {_AWS}\n", encoding="utf-8")
        findings = scan(tmp_path)
        assert len(findings) == 1
        assert findings[0][2] == "AWS Access Key"

    def test_detects_pat(self, tmp_path: Path):
        bad = tmp_path / "note.md"
        bad.write_text(f"token = {_PAT}\n", encoding="utf-8")
        findings = scan(tmp_path)
        assert any(f[2] == "GitHub PAT" for f in findings)

    def test_detects_private_key(self, tmp_path: Path):
        bad = tmp_path / "id_rsa"
        bad.write_text("-----BEGIN RSA PRIVATE" + " KEY-----\nabc\n", encoding="utf-8")
        findings = scan(tmp_path)
        assert any(f[2] == "Private key block" for f in findings)

    def test_detects_password_assignment(self, tmp_path: Path):
        bad = tmp_path / "settings.ini"
        bad.write_text(f"secret = '{_PW}'\n", encoding="utf-8")
        findings = scan(tmp_path)
        assert any(f[2] == "Generic secret assignment" for f in findings)

    def test_skips_binary(self, tmp_path: Path):
        binary = tmp_path / "blob.bin"
        binary.write_bytes(b"\xff\xfe\x00AKIA123")
        assert scan(tmp_path) == []

    def test_skips_cache_dirs(self, tmp_path: Path):
        cache = tmp_path / "__pycache__" / "mod.py"
        cache.parent.mkdir()
        cache.write_text(f"secret = '{_PW}x'\n", encoding="utf-8")
        assert scan(tmp_path) == []


class TestMain:
    def test_exit_zero_on_clean(self, tmp_path: Path, capsys):
        assert main(["prog", str(tmp_path)]) == 0
        assert "clean" in capsys.readouterr().out

    def test_exit_one_on_findings(self, tmp_path: Path):
        bad = tmp_path / "cfg.txt"
        bad.write_text("-----BEGIN PRIVATE" + " KEY-----\n", encoding="utf-8")
        assert main(["prog", str(tmp_path)]) == 1
