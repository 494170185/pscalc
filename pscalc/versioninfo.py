"""版本与构建信息（工具链）。

暴露给 report 与 CLI 的版本聚合点：
  version_info()      完整版本信息（版本号 + Python 版本）
  changelog_head()    CHANGELOG.md 最近一个版本段的标题

README 徽章与 pscalc version 输出共用。
"""
from __future__ import annotations

import sys
from pathlib import Path

from . import __version__

_CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"


def version_info() -> dict[str, str]:
    """版本聚合信息。"""
    return {
        "pscalc": __version__,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}."
        f"{sys.version_info.micro}",
    }


def changelog_head() -> str | None:
    """CHANGELOG.md 中最近一个版本段标题（如 [0.1.0] - 2026-09-24）。

    文件不存在时返回 None（可分发包场景）。
    """
    if not _CHANGELOG.exists():
        return None
    for line in _CHANGELOG.read_text(encoding="utf-8").splitlines():
        if line.startswith("## ["):
            return line.strip("# ").strip()
    return None


def banner() -> str:
    """CLI 启动横幅文本。"""
    info = version_info()
    return f"pscalc {info['pscalc']} (Python {info['python']})"
