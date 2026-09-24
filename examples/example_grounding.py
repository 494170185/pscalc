"""示例：接地网设计与校验。

    python examples/example_grounding.py
"""
from pscalc.grounding import (
    GridParams,
    check_grounding,
    grid_resistance,
)


def main() -> None:
    grid = GridParams(area_m2=80 * 60, total_length_m=2600)
    rho = 120.0
    rg = grid_resistance(rho, grid)
    print(f"土壤 ρ={rho} Ω·m，网格 {80}×{60} m")
    print(f"接地电阻 Rg = {rg:.3f} Ω")
    for c in check_grounding(
        rho_ohm_m=rho,
        grid=grid,
        ig_a=800,
        est_touch_v=180,
        est_step_v=260,
        rho_s=rho,
        t_s=0.4,
        target_rg_ohm=1.0,
    ):
        print(c.summary())

if __name__ == "__main__":
    main()
