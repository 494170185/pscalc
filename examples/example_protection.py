"""示例：继电保护整定三段式。

    python examples/example_protection.py
"""
from pscalc.protection import (
    CTParams,
    check_sensitivity,
    instantaneous_pickup,
    overload_pickup,
    relay_settings,
    timed_pickup,
)


def main() -> None:
    ct = CTParams(primary_a=600)
    iop1 = instantaneous_pickup(9.0)
    iop2 = timed_pickup(iop1)
    iop3 = overload_pickup(450.0)
    print(f"Ⅰ段（速断）: {iop1:.2f} kA → 二次 {relay_settings(iop1 * 1000, ct):.1f} A")
    print(f"Ⅱ段（限时速断）: {iop2:.2f} kA → 二次 {relay_settings(iop2 * 1000, ct):.1f} A")
    print(f"Ⅲ段（过负荷）: {iop3 / 1000:.2f} kA → 二次 {relay_settings(iop3, ct):.1f} A")
    c = check_sensitivity(6.5, iop2, minimum=1.3)
    print(c.summary())

if __name__ == "__main__":
    main()
