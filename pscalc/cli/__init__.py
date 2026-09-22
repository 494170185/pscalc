"""pscalc.cli —— 命令行包。

main() 在 cli/main.py；`python -m pscalc.cli` 走 __main__。
"""
from __future__ import annotations

import sys

from .main import main

if __name__ == "__main__":
    sys.exit(main())
