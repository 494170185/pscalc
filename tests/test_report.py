"""M12：计算书生成。"""
from pathlib import Path

from pscalc.elements import LineParams, SourceParams, TransformerParams
from pscalc.equipment import EquipmentCheck
from pscalc.network import Network
from pscalc.perunit import SystemBase
from pscalc.powerflow import solve
from pscalc.report import build_report, save_report
from pscalc.shortcircuit import fault_currents


def build_net() -> Network:
    net = Network(SystemBase(s_mva=100.0, base_kv=115.0))
    net.add_bus("G", 115.0, is_source=True)
    net.add_bus("A", 115.0)
    net.add_bus("B", 10.0)
    net.add_source("G", SourceParams(sk_mva=2000))
    net.add_line("G", "A", LineParams(0.1, 0.4, 30))
    net.add_transformer("A", "B", TransformerParams(sn_mva=50, uk_percent=10.5, pk_kw=210))
    return net


def full_results():
    net = build_net()
    faults = fault_currents(net)
    pf = solve(net, {"B": (30.0, 10.0)}, "G")
    checks = [
        EquipmentCheck("断路器开断（Ik''）", True, 12.5),
        EquipmentCheck("母线热稳定截面", False, -8.0),
    ]
    return net, faults, pf, checks


class TestBuildReport:
    def test_title_present(self):
        net, faults, pf, checks = full_results()
        text = build_report("110 kV 变电站短路电流计算书", net, faults, pf, checks)
        assert text.startswith("# 110 kV 变电站短路电流计算书")

    def test_sections_present(self):
        net, faults, pf, checks = full_results()
        text = build_report("t", net, faults, pf, checks)
        for section in ("工程概况", "短路电流计算", "潮流与电压", "设备校验汇总", "口径说明"):
            assert section in text

    def test_all_buses_in_fault_table(self):
        net, faults, pf, checks = full_results()
        text = build_report("t", net, faults, pf, checks)
        for bus in ("G", "A", "B"):
            assert f"| {bus} " in text

    def test_missing_pf_omitted(self):
        net, faults, _, _ = full_results()
        text = build_report("t", net, faults, None, None)
        assert "潮流与电压" not in text
        assert "设备校验" not in text

    def test_check_summary_lines(self):
        net, faults, pf, checks = full_results()
        text = build_report("t", net, faults, pf, checks)
        assert "通过 1 项" in text
        assert "不通过" in text

    def test_numbers_formatted(self):
        net, faults, pf, checks = full_results()
        text = build_report("t", net, faults, pf, checks)
        # 电流 3 位小数（表格里应有形如 x.xxx 的数）
        assert any(
            part.count(".") == 1 and len(part.split(".")[1]) == 3
            for line in text.splitlines()
            for part in line.replace("|", " ").split()
        )


class TestSaveReport:
    def test_write_and_read(self, tmp_path: Path):
        net, faults, _, _ = full_results()
        text = build_report("t", net, faults)
        out = save_report(text, tmp_path / "sub" / "report.md")
        assert out.exists()
        assert out.read_text(encoding="utf-8") == text

    def test_creates_parent_dirs(self, tmp_path: Path):
        out = save_report("# hi\n", tmp_path / "a" / "b" / "c.md")
        assert out.exists()


def test_report_is_pure_text():
    """报告是字符串（方便管道与测试），不依赖外部模板。"""
    net, faults, _, _ = full_results()
    assert isinstance(build_report("t", net, faults), str)
