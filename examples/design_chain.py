"""跨模块综合案例（M28）：一条完整设计链路。

从同一网络出发：短路 → 校验（断路器/电缆）→ 潮流 →
电压损耗 → 无功补偿建议 → 报告。作为各模块协同的
集成测试与端到端示例。
"""
from __future__ import annotations

from pscalc.compensation import cap_bank_size, compensate_effect
from pscalc.elements import LineParams, SourceParams, TransformerParams
from pscalc.equipment import BreakerRating, CableRating, check_breaker, check_cable
from pscalc.network import Network
from pscalc.perunit import SystemBase
from pscalc.powerflow import solve
from pscalc.report import build_report
from pscalc.shortcircuit import fault_currents
from pscalc.voltagedrop import voltage_drop


def build_case_network() -> Network:
    """110 kV 终端变：电源 20 km 线路 → 50 MVA 主变 → 10 kV。"""
    base = SystemBase(s_mva=100.0, base_kv=115.0)
    net = Network(base)
    net.add_bus("G", 110.0, is_source=True)
    net.add_bus("HV", 110.0)
    net.add_bus("LV", 10.5)
    net.add_source("G", SourceParams(sk_mva=2000))
    net.add_line("G", "HV", LineParams(0.132, 0.4, 20))
    net.add_transformer("HV", "LV", TransformerParams(50, 10.5, 210))
    return net


def design_chain() -> dict:
    """跑完整条设计链，返回各环节关键结果。"""
    net = build_case_network()

    faults = fault_currents(net)
    lv_fault = faults["LV"]

    breaker = BreakerRating(
        rated_breaking_ka=25.0, rated_peak_ka=63.0, rated_thermal_ka=25.0
    )
    breaker_checks = check_breaker(
        breaker,
        ikss_ka=lv_fault.ikss_ka,
        ip_ka=lv_fault.ip_ka,
        ith_ka=lv_fault.ith_ka,
        tk_s=1.0,
    )
    # 10 kV 侧 30 MW 经 5 回电缆分摊（每回 6 MW ≈ 330 A < 400 A）
    cable = CableRating(area_mm2=240, k_factor=142, ampacity_a=400)
    load_a_per_feeder = 6.0e6 / (3**0.5 * 10.5e3)
    cable_checks = check_cable(
        cable, ith_ka=lv_fault.ith_ka, tk_s=0.5, load_current_a=load_a_per_feeder
    )

    pf = solve(net, {"LV": (30.0, 10.0)}, "G")
    drop_pct = voltage_drop(pf, "LV", "G")

    q_need_kvar = cap_bank_size(30.0, 0.95, 0.98)
    eff = compensate_effect(30.0, 10.0, q_need_kvar / 1000)

    report = build_report(
        "综合设计链路示例", net, faults, pf, breaker_checks + cable_checks
    )

    return {
        "ikss_lv": lv_fault.ikss_ka,
        "breaker_ok": all(c.ok for c in breaker_checks),
        "cable_ok": all(c.ok for c in cable_checks),
        "v_drop_pct": drop_pct,
        "q_need_kvar": q_need_kvar,
        "pf_after": eff.pf_after,
        "report_len": len(report),
        "report_has_sections": all(
            s in report for s in ("短路电流计算", "潮流与电压", "设备校验汇总")
        ),
    }
