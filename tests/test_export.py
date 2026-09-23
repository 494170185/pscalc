"""M23：结果导出。"""
import json

import pytest

from pscalc.export import fault_rows, load_rows, to_csv, to_json
from pscalc.shortcircuit import fault_currents
from tests.test_shortcircuit import build_net


def make_results():
    net = build_net()
    return fault_currents(net)


class TestFaultRows:
    def test_sorted_by_bus(self):
        rows = fault_rows(make_results())
        assert [r["bus"] for r in rows] == sorted(r["bus"] for r in rows)

    def test_fields_complete(self):
        rows = fault_rows(make_results())
        for row in rows:
            assert set(row) >= {
                "bus", "ikss_ka", "ip_ka", "sk_mva",
            }

    def test_values_match(self):
        results = make_results()
        rows = fault_rows(results)
        by_bus = {r["bus"]: r for r in rows}
        assert by_bus["G"]["ikss_ka"] == pytest.approx(results["G"].ikss_ka)


class TestCsv:
    def test_roundtrip(self):
        rows = fault_rows(make_results())
        text = to_csv(rows)
        back = load_rows(text)
        assert len(back) == len(rows)
        assert back[0]["bus"] == rows[0]["bus"]

    def test_header_line(self):
        text = to_csv(fault_rows(make_results()))
        first = text.splitlines()[0]
        assert "ikss_ka" in first

    def test_empty_rows_empty_text(self):
        assert to_csv([]) == ""

    def test_heterogeneous_fields_union(self):
        rows = [{"a": 1}, {"b": 2}]
        text = to_csv(rows)
        assert "a,b" in text.splitlines()[0]


class TestToJson:
    def test_dataclass_exported(self):
        results = make_results()
        payload = json.loads(to_json(results))
        assert "G" in payload
        assert payload["G"]["ikss_ka"] == pytest.approx(results["G"].ikss_ka)

    def test_plain_dict(self):
        assert json.loads(to_json({"a": 1})) == {"a": 1}

    def test_list_passthrough(self):
        assert json.loads(to_json([1, 2])) == [1, 2]
