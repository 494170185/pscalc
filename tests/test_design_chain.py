"""M28：端到端综合设计链集成测试。"""

from examples.design_chain import build_case_network, design_chain


class TestDesignChain:
    def test_network_valid(self):
        net = build_case_network()
        assert net.validate() == []
        assert set(net.buses) == {"G", "HV", "LV"}

    def test_fault_reasonable(self):
        results = design_chain()
        # 10 kV 侧 Ik'' 在 5-30 kA 的工程合理区间
        assert 5 < results["ikss_lv"] < 30

    def test_equipment_checks(self):
        results = design_chain()
        assert results["breaker_ok"]
        assert results["cable_ok"]

    def test_voltage_drop_positive(self):
        results = design_chain()
        assert 0 < results["v_drop_pct"] < 20

    def test_compensation_improves_pf(self):
        results = design_chain()
        assert results["pf_after"] > 0.95

    def test_report_sections(self):
        results = design_chain()
        assert results["report_has_sections"]
        assert results["report_len"] > 500


def test_design_chain_is_deterministic():
    a = design_chain()
    b = design_chain()
    assert a == b
