"""pscalc.cli.export —— 结果导出子命令。

  pscalc export <scenario> --format csv   短路表 → CSV
  pscalc export <scenario> --format json  短路结果 → JSON
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ..export import fault_rows, to_csv, to_json
from ..scenarios import load_scenario
from ..shortcircuit import fault_currents
from .check import resolve


def run_export(name: str, fmt: str, output: str | None) -> str:
    """导出场景短路结果，返回文本（写文件由调用方决定）。"""
    if fmt not in ("csv", "json"):
        raise ValueError("format 只支持 csv/json")
    path = resolve(name)
    net, _loads = load_scenario(path)
    faults = fault_currents(net)

    if fmt == "csv":
        text = to_csv(fault_rows(faults))
    else:
        text = to_json(faults)

    if output:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return text


def add_export_args(parser: argparse.ArgumentParser) -> None:
    """export 子命令的参数。"""
    parser.add_argument("scenario", help="场景 JSON 路径或内置场景名")
    parser.add_argument("--format", default="csv", choices=["csv", "json"])
    parser.add_argument("-o", "--output", help="输出到文件（默认打印）")
