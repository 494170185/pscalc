"""示例：无功补偿选型。

    python examples/example_compensation.py
"""
from pscalc.compensation import auto_config, cap_bank_size, compensate_effect


def main() -> None:
    p_mw, current_pf, target_pf = 10.0, 0.82, 0.95
    need_kvar = cap_bank_size(p_mw, current_pf, target_pf)
    cfg = auto_config(need_kvar, unit_kvar=100, max_units=8)
    print(f"负荷 {p_mw} MW，cosφ {current_pf} → {target_pf}")
    print(f"需要补偿: {need_kvar:.0f} kvar")
    print(f"配置: {cfg.units} × {cfg.unit_kvar} kvar = {cfg.total_kvar():.0f} kvar")
    eff = compensate_effect(p_mw, p_mw * 0.7, cfg.total_kvar() / 1000)
    print(f"补偿后: cosφ={eff.pf_after:.3f}，Q 剩余 {eff.q_after_mvar:.2f} Mvar")

if __name__ == "__main__":
    main()
