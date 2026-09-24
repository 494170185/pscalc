"""pscalc.cli.main —— 命令行入口（pyproject [project.scripts] 指向这里）。

  pscalc scenarios            列出内置场景
  pscalc run <scenario>       跑一个场景并打印计算书
  pscalc run <s> -o out.md    写文件
  pscalc check <scenario>     场景自检（加载/拓扑/短路/潮流）
  pscalc export <s> [--format csv|json]   短路结果导出
  pscalc version              版本
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import __version__
from ..scenarios import list_scenarios, run_scenario
from .check import run_check
from .export import add_export_args, run_export


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pscalc",
        description="变电站一次设计计算：短路电流（IEC 60909）、辐射网潮流、无功补偿与设备校验",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("scenarios", help="列出内置场景")
    sub.add_parser("version", help="显示版本")

    run = sub.add_parser("run", help="运行场景并生成计算书")
    run.add_argument("scenario", help="场景 JSON 路径或内置场景名")
    run.add_argument("-o", "--output", help="输出到文件（默认打印）")
    run.add_argument("--title", help="报告标题")

    check = sub.add_parser("check", help="场景自检（加载/拓扑/短路/潮流）")
    check.add_argument("scenario", help="场景 JSON 路径或内置场景名")

    export = sub.add_parser("export", help="导出短路结果")
    add_export_args(export)

    return parser


def _resolve_scenario(name: str) -> Path:
    """场景名 → 内置文件路径；已是路径则原样返回。"""
    p = Path(name)
    if p.exists():
        return p
    for f in list_scenarios():
        if f.stem == name:
            return f
    raise SystemExit(f"找不到场景: {name}（不是文件，也不是内置场景名）")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print(f"pscalc {__version__}")
        return 0

    if args.command == "scenarios":
        files = list_scenarios()
        if not files:
            print("（无内置场景）")
            return 0
        for f in files:
            print(f.stem)
        return 0

    if args.command == "run":
        path = _resolve_scenario(args.scenario)
        text = run_scenario(path, title=args.title)
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            print(f"计算书已写入 {out}")
        else:
            print(text)
        return 0

    if args.command == "check":
        ok, messages = run_check(args.scenario)
        for msg in messages:
            print(msg)
        print("自检通过" if ok else "自检未通过")
        return 0 if ok else 1

    if args.command == "export":
        text = run_export(args.scenario, args.format, args.output)
        if args.output:
            print(f"结果已导出到 {args.output}")
        else:
            print(text)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
