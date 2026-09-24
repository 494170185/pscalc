"""examples/ 目录脚本可执行性测试（每个脚本跑一遍不崩即过）。"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = sorted(Path(__file__).parent.parent.glob("examples/example_*.py"))


@pytest.mark.parametrize("script", EXAMPLES, ids=lambda p: p.stem)
def test_example_runs(script: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(script.parent.parent)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        cwd=script.parent.parent,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip(), "脚本应有输出"


def test_examples_directory_exists():
    assert len(EXAMPLES) >= 8
