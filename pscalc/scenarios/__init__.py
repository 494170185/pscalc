"""场景库（M13）：JSON 定义典型接线，加载即算。

  scenarios/            内置场景文件（见同目录 *.json）
  load_scenario(path)   JSON → Network + loads
  list_scenarios()      内置场景清单
  run_scenario(path)    一键：加载 → 短路 + 潮流 + 报告

JSON 结构（约定见 docs/scenario-format.md）：
  {"base": {"s_mva": 100, "kv": 115},
   "buses": [{"name": "G", "kv": 115, "source": {"sk_mva": 2000}}, ...],
   "branches": [{"type": "line", "from": "G", "to": "A",
                 "r": 0.1, "x": 0.4, "km": 30}, ...],
   "loads": {"B": [30.0, 10.0]}}
"""
from __future__ import annotations

import json
from pathlib import Path

from ..elements import LineParams, SourceParams, TransformerParams
from ..network import Network
from ..perunit import SystemBase
from ..powerflow import solve as pf_solve
from ..report import build_report
from ..shortcircuit import fault_currents

SCENARIO_DIR = Path(__file__).parent


def list_scenarios() -> list[Path]:
    """内置场景清单（*.json）。"""
    if not SCENARIO_DIR.exists():
        return []
    return sorted(SCENARIO_DIR.glob("*.json"))


def load_scenario(path: str | Path) -> tuple[Network, dict[str, tuple[float, float]]]:
    """JSON → (Network, loads)。

    校验失败抛 ScenarioError（带字段路径，方便定位）。
    """
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    try:
        base = SystemBase(
            s_mva=float(data["base"]["s_mva"]), base_kv=float(data["base"]["kv"])
        )
        net = Network(base)
        for bus in data["buses"]:
            has_source = "source" in bus
            net.add_bus(bus["name"], float(bus["kv"]), is_source=has_source)
            if has_source:
                src = bus["source"]
                net.add_source(
                    bus["name"],
                    SourceParams(
                        sk_mva=src.get("sk_mva"),
                        ikss_ka=src.get("ikss_ka"),
                        voltage_kv=float(bus["kv"]),
                    ),
                )
        for br in data["branches"]:
            kind = br["type"]
            if kind == "line":
                net.add_line(
                    br["from"], br["to"],
                    LineParams(float(br["r"]), float(br["x"]), float(br["km"])),
                )
            elif kind == "transformer":
                net.add_transformer(
                    br["from"], br["to"],
                    TransformerParams(
                        sn_mva=float(br["sn"]),
                        uk_percent=float(br["uk"]),
                        pk_kw=float(br.get("pk", 0)),
                    ),
                )
            else:
                raise ScenarioError(f"未知支路类型 {kind}")
        loads = {
            name: (float(v[0]), float(v[1]))
            for name, v in data.get("loads", {}).items()
        }
    except KeyError as exc:
        raise ScenarioError(f"缺少必需字段: {exc}") from exc
    except (TypeError, ValueError) as exc:
        raise ScenarioError(f"字段类型错误: {exc}") from exc
    problems = net.validate()
    if problems:
        raise ScenarioError("拓扑自检失败: " + "; ".join(problems))
    return net, loads


def run_scenario(path: str | Path, title: str | None = None) -> str:
    """加载场景并产出完整计算书文本。"""
    net, loads = load_scenario(path)
    if title is None:
        title = Path(path).stem + " 短路电流与潮流计算书"
    faults = fault_currents(net)
    pf = pf_solve(net, loads, _slack_of(net))
    return build_report(title, net, faults, pf)


def _slack_of(net: Network) -> str:
    for name, bus in net.buses.items():
        if bus.is_source:
            return name
    raise ScenarioError("场景没有电源母线")


class ScenarioError(ValueError):
    """场景文件结构/字段错误。"""
