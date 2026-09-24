"""示例：可靠性指标计算。

    python examples/example_reliability.py
"""
from pscalc.reliability import OutageEvent, all_indices


def main() -> None:
    events = [
        OutageEvent(customers=300, hours=1.5, avg_load_mw=4.0),
        OutageEvent(customers=120, hours=3.0, avg_load_mw=2.0),
        OutageEvent(customers=450, hours=0.5, avg_load_mw=6.0),
    ]
    idx = all_indices(events, total_customers=2000)
    print(f"SAIFI = {idx['saifi']:.3f} 次/户·年")
    print(f"SAIDI = {idx['saidi']:.3f} 时/户·年")
    print(f"CAIDI = {idx['caidi']:.2f} 时/次")
    print(f"ASAI  = {idx['asai'] * 100:.4f}%")
    print(f"缺供电量 = {idx['enr_mwh']:.1f} MWh")

if __name__ == "__main__":
    main()
