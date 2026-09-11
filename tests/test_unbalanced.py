"""M6：单相接地与两相短路。"""
import pytest

from pscalc.elements import LineParams, SourceParams, TransformerParams
from pscalc.network import Network
from pscalc.perunit import SystemBase
from pscalc.unbalanced import (
    SequenceImpedances,
    sequence_impedances,
    single_phase_earth_fault,
    two_phase_fault,
)

BASE = SystemBase(s_mva=100.0, base_kv=115.0)


def build_net(zero: dict[str, tuple[float, float]] | None = None) -> Network:
    net = Network(BASE)
    net.add_bus("G", 115.0, is_source=True)
    net.add_bus("A", 115.0)
    net.add_bus("B", 10.0)
    net.add_source("G", SourceParams(sk_mva=2000))
    net.add_line("G", "A", LineParams(0.1, 0.4, 30))
    net.add_transformer("A", "B", TransformerParams(sn_mva=50, uk_percent=10.5, pk_kw=210))
    if zero:
        net.zero_sequence = zero
    return net


class TestSequenceImpedances:
    def test_z2_equals_z1(self):
        net = build_net()
        seq = sequence_impedances(net, "A")
        assert seq.z2 == seq.z1

    def test_ungrounded_when_missing(self):
        net = build_net()
        seq = sequence_impedances(net, "B")
        assert seq.is_ungrounded()

    def test_zero_from_dict(self):
        net = build_net(zero={"B": (0.01, 0.35)})
        seq = sequence_impedances(net, "B")
        assert seq.z0 == complex(0.01, 0.35)


class TestSinglePhase:
    def test_ungrounded_zero_current(self):
        net = build_net()
        ik1, _ = single_phase_earth_fault(net, "G", 1.1)
        assert ik1 == 0.0

    def test_grounded_matches_formula(self):
        net = build_net(zero={"G": (0.0, 0.1)})
        ik1, seq = single_phase_earth_fault(net, "G", 1.1)
        z1 = net.bus_impedance("G")
        z_sum = complex(*z1) * 2 + complex(0.0, 0.1)
        i_pu = 3 * 1.1 / abs(z_sum)
        i_base = 100 / (3**0.5 * 115)
        assert ik1 == pytest.approx(i_pu * i_base, rel=1e-6)
        assert seq.z0 is not None

    def test_larger_z0_smaller_current(self):
        net_small = build_net(zero={"B": (0.01, 0.2)})
        net_large = build_net(zero={"B": (0.01, 0.8)})
        ik_small, _ = single_phase_earth_fault(net_small, "B", 1.05)
        ik_large, _ = single_phase_earth_fault(net_large, "B", 1.05)
        assert ik_large < ik_small


class TestTwoPhase:
    def test_matches_formula(self):
        net = build_net()
        ik2, _ = two_phase_fault(net, "G", 1.1)
        r, x = net.bus_impedance("G")
        z_sum = complex(r, x) * 2
        i_pu = 3**0.5 * 1.1 / abs(z_sum)
        i_base = 100 / (3**0.5 * 115)
        assert ik2 == pytest.approx(i_pu * i_base, rel=1e-6)

    def test_two_phase_vs_three_phase_ratio(self):
        """远端故障（Z1=Z2 时 Ik2 ≈ 0.87·Ik3）。"""
        import math

        from pscalc.shortcircuit import short_circuit

        net = build_net()
        ik2, _ = two_phase_fault(net, "A", 1.1)
        ik3 = short_circuit(net, "A").ikss_ka
        assert ik2 / ik3 == pytest.approx(math.sqrt(3) / 2, rel=1e-6)


def test_result_dataclass_is_frozen():
    seq = SequenceImpedances(z1=1 + 1j, z2=1 + 1j, z0=None)
    with pytest.raises(Exception):  # noqa: B017
        seq.z1 = 2j  # type: ignore[misc]
