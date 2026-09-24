"""示例：经济截面选择。

    python examples/example_economic.py
"""
from pscalc.economic import CostParams, choose_conductor, economic_section


def main() -> None:
    imax, hours = 320.0, 4500.0
    s = economic_section(imax, "al", hours)
    params = CostParams(
        investment_per_mm2=180.0,
        loss_price_yuan_per_kwh=0.55,
        resistance_per_mm2_km=31.5,
    )
    chosen = choose_conductor(imax, "al", hours, 12.0, params)
    print(f"Imax={imax} A，Tmax={hours} h（铝）")
    print(f"经济截面 S = {s:.1f} mm²，年费用比较后选择 LGJ-{chosen:.0f}")

if __name__ == "__main__":
    main()
