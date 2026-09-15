"""辐射网潮流（M8）：前推回代法。

辐射网（树形）潮流不用牛顿-拉夫逊，前推回代（backward/
forward sweep）迭代少且稳：

  solve(net, loads, slack)   一次潮流：各母线电压（pu）、
                              支路功率（MVA）、网损
  BranchFlow                 支路首端/末端功率与电流
  PowerFlowResult            全网结果

负荷（M4 的 Load）挂在母线上；平衡节点取电源母线，
电压 = 1.0 pu（源侧无调节）。收敛判据：电压修正量
最大值 < eps（默认 1e-6）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .network import Network


@dataclass(frozen=True)
class BranchFlow:
    """支路潮流：首端（靠电源）与末端功率。"""

    from_bus: str
    to_bus: str
    p_from_mw: float
    q_from_mvar: float
    p_to_mw: float
    q_to_mvar: float
    i_ka: float

    def loss_mw(self) -> float:
        return self.p_from_mw - self.p_to_mw


@dataclass(frozen=True)
class PowerFlowResult:
    """潮流结果：母线电压（pu，以本级额定电压为基准）。"""

    voltages: dict[str, float]
    branch_flows: list[BranchFlow]
    total_loss_mw: float
    iterations: int
    converged: bool

    def min_voltage_bus(self) -> tuple[str, float]:
        """电压最低的母线（名, pu）。"""
        if not self.voltages:
            raise ValueError("空结果")
        name = min(self.voltages, key=self.voltages.get)  # type: ignore[arg-type]
        return name, self.voltages[name]


@dataclass
class _PfContext:
    net: Network
    loads: dict[str, tuple[float, float]]
    slack: str
    children: dict[str, list[str]] = field(default_factory=dict)
    parent: dict[str, str] = field(default_factory=dict)


def _build_tree(ctx: _PfContext) -> None:
    """以 slack 为根建树（忽略电源内节点）。"""
    ctx.parent = {ctx.slack: ""}
    queue = [ctx.slack]
    ctx.children = {ctx.slack: []}
    while queue:
        cur = queue.pop(0)
        for br in ctx.net._adj.get(cur, []):
            other = br.to_bus if br.from_bus == cur else br.from_bus
            if other.startswith("__") or other in ctx.parent:
                continue
            ctx.parent[other] = cur
            ctx.children.setdefault(cur, []).append(other)
            ctx.children.setdefault(other, [])
            queue.append(other)


def _branch_between(ctx: _PfContext, a: str, b: str):
    for br in ctx.net._adj.get(a, []):
        other = br.to_bus if br.from_bus == a else br.from_bus
        if other == b and br.kind != "source":
            return br
    raise KeyError(f"找不到 {a}-{b} 支路")


def solve(
    net: Network,
    loads: dict[str, tuple[float, float]],
    slack: str,
    eps: float = 1e-6,
    max_iter: int = 100,
) -> PowerFlowResult:
    """前推回代潮流。loads = {母线: (P_mw, Q_mvar)}。"""
    problems = net.validate()
    if problems:
        raise ValueError("网络拓扑未通过自检: " + "; ".join(problems))
    if slack not in net.buses:
        raise KeyError(f"平衡节点 {slack} 不存在")

    ctx = _PfContext(net=net, loads=loads, slack=slack)
    _build_tree(ctx)

    # 初始电压 1.0
    v = {name: 1.0 + 0j for name in net.buses}
    converged = False
    iterations = 0

    for it in range(max_iter):
        iterations = it + 1
        # ---- 回推（backward）：从叶到根累计功率 ----
        # s_req[b] = 负荷 + 下游需求（用上轮电压近似损耗）
        s_req: dict[str, complex] = {}
        for name in net.buses:
            p, q = loads.get(name, (0.0, 0.0))
            s_req[name] = complex(p, q)

        # 按树的逆拓扑序（叶→根）
        order = []
        stack = [slack]
        while stack:
            cur = stack.pop()
            order.append(cur)
            stack.extend(ctx.children.get(cur, []))
        for node in reversed(order):
            if node == slack:
                continue
            par = ctx.parent[node]
            br = _branch_between(ctx, par, node)
            z_pu = complex(br.r_pu, br.x_pu)
            # 支路首端功率 = 需求 + 损耗（用本级电压近似）
            s_down = s_req[node]
            v_node = max(abs(v[node]), 0.1)
            # 支路电流（pu，按 S/V）；电压为 pu，S 为 pu 化后
            s_pu = s_down / net.base.s_mva
            i_pu = abs(s_pu / v_node)
            loss_pu = abs(i_pu) ** 2 * z_pu
            s_req[par] += s_pu + loss_pu * net.base.s_mva

        # ---- 前推（forward）：从根到叶更新电压 ----
        v_new = {slack: 1.0 + 0j}
        for node in order:
            if node == slack:
                continue
            par = ctx.parent[node]
            br = _branch_between(ctx, par, node)
            z_pu = complex(br.r_pu, br.x_pu)
            s_head = s_req[node] / net.base.s_mva
            # I = conj(S)/conj(V)（S=V·I*），保证感性负荷 QX 压降为正
            i_pu = s_head.conjugate() / v_new[par].conjugate()
            v_new[node] = v_new[par] - i_pu * z_pu

        diff = max(abs(v_new[n] - v[n]) for n in net.buses)
        v = v_new
        if diff < eps:
            converged = True
            break

    # ---- 支路潮流整理 ----
    flows: list[BranchFlow] = []
    total_loss = 0.0
    for node in order:
        if node == slack:
            continue
        par = ctx.parent[node]
        br = _branch_between(ctx, par, node)
        s_head = s_req[node] / net.base.s_mva
        # 电流（pu）= 首端功率 / 首端电压共轭，转 kA 用故障母线基准
        i_pu = abs(s_head / max(abs(v[par]), 0.1))
        loss = i_pu**2 * complex(br.r_pu, br.x_pu)
        i_base = net.base.s_mva / (3**0.5 * net.buses[node].kv)
        flows.append(
            BranchFlow(
                from_bus=par,
                to_bus=node,
                p_from_mw=s_head.real * net.base.s_mva,
                q_from_mvar=s_head.imag * net.base.s_mva,
                p_to_mw=(s_head.real - loss.real) * net.base.s_mva,
                q_to_mvar=(s_head.imag - loss.imag) * net.base.s_mva,
                i_ka=i_pu * i_base,
            )
        )
        total_loss += loss.real * net.base.s_mva

    return PowerFlowResult(
        voltages={n: abs(vv) for n, vv in v.items()},
        branch_flows=flows,
        total_loss_mw=total_loss,
        iterations=iterations,
        converged=converged,
    )
