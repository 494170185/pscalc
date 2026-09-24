"""示例：设备校验链。

    python examples/example_equipment.py
"""
from pscalc.equipment import (
    BreakerRating,
    CableRating,
    check_breaker,
    check_cable,
)


def main() -> None:
    breaker = BreakerRating(
        rated_breaking_ka=31.5, rated_peak_ka=80, rated_thermal_ka=31.5
    )
    for c in check_breaker(breaker, ikss_ka=20.0, ip_ka=48.0, ith_ka=22.0, tk_s=1.0):
        print(c.summary())

    cable = CableRating(area_mm2=185, k_factor=142, ampacity_a=340)
    for c in check_cable(cable, ith_ka=18.0, tk_s=0.5, load_current_a=300):
        print(c.summary())

if __name__ == "__main__":
    main()
