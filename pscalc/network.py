"""网络拓扑（M3）：母线、支路与图遍历。

Network 把 M2 的元件挂到母线上，形成可计算的拓扑：
  add_bus / add_line / add_transformer / add_source
  bus_impedance(fault_bus)    母线对地的戴维南等值阻抗（pu），
                              从电源侧沿最短路径累积（辐射网口径）
  connected_buses(start)      BFS 连通片
  validate()                  拓扑自检（孤立母线/重复支路）

多电源辐射网的叠加：bus_impedance 把各电源到故障点的
路径阻抗并联（仅适合辐射网；环网在 M13 场景库中显式排除）。
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from itertools import pairwise

from .elements import (
    LineParams,
    SourceParams,
    TransformerParams,
    line_pu,
    source_pu,
    transformer_pu,
)
from .perunit import SystemBase


@dataclass
class Bus:
    """母线：名称、电压等级、编号。"""

    name: str
    kv: float
    id: int = -1
    is_source: bool = False


@dataclass
class Branch:
    """支路：线路或变压器（起止母线 + 标幺值阻抗）。"""

    from_bus: str
    to_bus: str
    r_pu: float
    x_pu: float
    kind: str  # "line" | "transformer" | "source"


class NetworkError(ValueError):
    """拓扑错误：未注册母线、重复支路、孤立节点等。"""


class Network:
    """辐射网模型（多电源允许，环网由 validate 拒绝）。"""

    def __init__(self, base: SystemBase) -> None:
        self.base = base
        self.buses: dict[str, Bus] = {}
        self.branches: list[Branch] = []
        self._adj: dict[str, list[Branch]] = {}
        self._source_buses: list[str] = []
        self._branch_keys: set[tuple[str, str, str]] = set()

    # ---- 构建 -------------------------------------------------------
    def add_bus(self, name: str, kv: float, is_source: bool = False) -> Bus:
        if name in self.buses:
            raise NetworkError(f"母线 {name} 已存在")
        if kv <= 0:
            raise NetworkError("母线电压必须为正")
        bus = Bus(name=name, kv=kv, id=len(self.buses), is_source=is_source)
        self.buses[name] = bus
        self._adj[name] = []
        if is_source:
            self._source_buses.append(name)
        return bus

    def _link(self, branch: Branch) -> None:
        self._check_bus(branch.from_bus)
        self._check_bus(branch.to_bus)
        key = self._branch_key(branch.from_bus, branch.to_bus, branch.kind)
        if key in self._branch_keys:
            raise NetworkError(f"支路 {branch.from_bus}-{branch.to_bus} 重复")
        self._branch_keys.add(key)
        self.branches.append(branch)
        self._adj[branch.from_bus].append(branch)
        self._adj[branch.to_bus].append(branch)

    @staticmethod
    def _branch_key(a: str, b: str, kind: str) -> tuple[str, str, str]:
        return (min(a, b), max(a, b), kind)

    def _check_bus(self, name: str) -> None:
        if name not in self.buses:
            raise NetworkError(f"母线 {name} 未注册")

    def add_line(self, from_bus: str, to_bus: str, params: LineParams) -> Branch:
        r, x = line_pu(params, self.base)
        branch = Branch(from_bus, to_bus, r, x, "line")
        self._link(branch)
        return branch

    def add_transformer(
        self, from_bus: str, to_bus: str, params: TransformerParams
    ) -> Branch:
        r, x = transformer_pu(params, self.base)
        branch = Branch(from_bus, to_bus, r, x, "transformer")
        self._link(branch)
        return branch

    def add_source(self, bus: str, params: SourceParams) -> Branch:
        """等值电源挂到母线（内阻抗记入支路，from=电源内节点）。"""
        self._check_bus(bus)
        inner = f"__src_{bus}"
        r, x = source_pu(params, self.base)
        branch = Branch(inner, bus, r, x, "source")
        # 电源内节点不进 buses 表，只进邻接表
        self._adj.setdefault(inner, [])
        self.branches.append(branch)
        self._adj[inner].append(branch)
        self._adj[bus].append(branch)
        if bus not in self._source_buses:
            self._source_buses.append(bus)
        return branch

    # ---- 查询 -------------------------------------------------------
    def connected_buses(self, start: str) -> list[str]:
        """从 start 出发 BFS 可达的母线（含 start）。"""
        self._check_bus(start)
        seen = {start}
        queue: deque[str] = deque([start])
        while queue:
            cur = queue.popleft()
            for br in self._adj.get(cur, []):
                other = br.to_bus if br.from_bus == cur else br.from_bus
                if other.startswith("__") or other in seen:
                    continue
                seen.add(other)
                queue.append(other)
        return sorted(seen)

    def bus_impedance(self, fault_bus: str) -> tuple[float, float]:
        """故障母线的戴维南等值 R+jX（pu，各电源路径并联）。

        路径 = 电源母线 → 故障母线沿网络最短路径的支路阻抗和。
        """
        self._check_bus(fault_bus)
        if not self._source_buses:
            raise NetworkError("网络没有电源")
        path_impedances: list[complex] = []
        for src in self._source_buses:
            if src == fault_bus:
                # 故障就在电源母线：只有内阻抗
                for br in self._adj[src]:
                    if br.kind == "source":
                        path_impedances.append(complex(br.r_pu, br.x_pu))
                continue
            path = self._shortest_path(src, fault_bus)
            if path is None:
                continue
            z = complex(br.r_pu, br.x_pu) if False else 0j
            for br in self._path_branches(path):
                z += complex(br.r_pu, br.x_pu)
            # 电源内阻抗也要计入该路径
            for br in self._adj[src]:
                if br.kind == "source" and br.to_bus == src:
                    z += complex(br.r_pu, br.x_pu)
            path_impedances.append(z)
        if not path_impedances:
            raise NetworkError(f"母线 {fault_bus} 与任何电源不连通")
        # 并联
        y = 0j
        for z in path_impedances:
            if z == 0:
                raise NetworkError("电源路径阻抗为零，无法求戴维南等值")
            y += 1 / z
        z_eq = 1 / y
        return z_eq.real, z_eq.imag

    def _shortest_path(self, start: str, goal: str) -> list[str] | None:
        """BFS 最短母线路径（不考虑电源内节点）。"""
        prev: dict[str, str | None] = {start: None}
        queue: deque[str] = deque([start])
        while queue:
            cur = queue.popleft()
            if cur == goal:
                break
            for br in self._adj.get(cur, []):
                other = br.to_bus if br.from_bus == cur else br.from_bus
                if other.startswith("__") or other in prev:
                    continue
                prev[other] = cur
                queue.append(other)
        if goal not in prev:
            return None
        path: list[str] = []
        cur: str | None = goal
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        return list(reversed(path))

    def _path_branches(self, path: list[str]) -> list[Branch]:
        out: list[Branch] = []
        for a, b in pairwise(path):
            found = None
            for br in self._adj[a]:
                other = br.to_bus if br.from_bus == a else br.from_bus
                if other == b and br.kind != "source":
                    found = br
                    break
            if found is None:
                raise NetworkError(f"找不到 {a}-{b} 之间的支路")
            out.append(found)
        return out

    # ---- 自检 -------------------------------------------------------
    def validate(self) -> list[str]:
        """返回拓扑问题清单（空列表 = 通过）。"""
        problems: list[str] = []
        if not self._source_buses:
            problems.append("没有电源母线")
        for name in self.buses:
            if not self._adj.get(name):
                problems.append(f"母线 {name} 没有任何支路（孤立）")
        if self._source_buses:
            reach = self.connected_buses(self._source_buses[0])
            for name in self.buses:
                if name not in reach:
                    problems.append(f"母线 {name} 与电源不连通")
        # 环网检测：支路数（不含电源）≥ 母线数 → 有环
        n_real = sum(1 for b in self.branches if b.kind != "source")
        if n_real >= len(self.buses):
            problems.append("检测到环网（支路数 ≥ 母线数），本库只支持辐射网")
        return problems


@dataclass
class Case:
    """一个计算案例：网络 + 运行方式（M4 起使用）。"""

    network: Network
    loads: dict[str, tuple[float, float]] = field(default_factory=dict)
    name: str = "case"
