"""敏感信息扫描（tools/check_secrets.py）。

CI 与提交前自检：扫描工作区文本文件中的密钥/令牌/凭据
特征。零发现 = 退出码 0。

  python tools/check_secrets.py [目录]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERNS: list[tuple[str, str]] = [
    ("AWS Access Key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("GitHub PAT", r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    (
        "Generic secret assignment",
        r"(?i)(secret|token|password|passwd|api[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    ),
    ("Private key block", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("Basic auth URL", r"[a-z][a-z0-9+.-]*://[^/@\s:]+:[^/@\s]+@[^\s]+"),
]

SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".ruff_cache",
    "node_modules", "build", "dist", ".venv", "htmlcov",
}
SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".zip", ".lock"}


def scan(root: Path) -> list[tuple[Path, int, str, str]]:
    """返回 [(文件, 行号, 规则名, 命中行)]。"""
    findings: list[tuple[Path, int, str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for name, pattern in PATTERNS:
                if re.search(pattern, line):
                    findings.append((path, lineno, name, line.strip()))
    return findings


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(".")
    findings = scan(root)
    if findings:
        for path, lineno, name, line in findings:
            print(f"{path}:{lineno}: [{name}] {line[:80]}")
        print(f"共 {len(findings)} 处疑似敏感信息，请清理后重试")
        return 1
    print("secrets scan: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
