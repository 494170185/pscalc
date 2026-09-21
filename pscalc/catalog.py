"""典型设备参数库（M20）。

把常用型谱参数集中成纯数据表，供选型/校验直接查：
  BREAKERS       断路器（10-500 kV 典型遮断/热稳/峰值）
  TRANSFORMERS   双绕组变压器（10/35/110 kV 常见容量档）
  CONDUCTORS     架空导线（LGJ 系列：载流量/直流电阻/截面）
  CABLES         交联聚乙烯电缆（YJV 系列）

  lookup(table, **filters)   按字段过滤查询
  nearest_capacity(table, needed)  容量就近选型

数据为工程典型值（公开手册口径），不是任何厂商铭牌。
"""
from __future__ import annotations

from dataclasses import dataclass

BREAKERS: tuple[dict, ...] = (
    {"model": "ZN63", "kv": 12, "breaking_ka": 31.5, "peak_ka": 80, "thermal_ka": 31.5},
    {"model": "LW25", "kv": 40.5, "breaking_ka": 31.5, "peak_ka": 80, "thermal_ka": 31.5},
    {"model": "LW36", "kv": 126, "breaking_ka": 31.5, "peak_ka": 80, "thermal_ka": 31.5},
    {"model": "LW10B", "kv": 252, "breaking_ka": 50, "peak_ka": 125, "thermal_ka": 50},
    {"model": "LW13", "kv": 550, "breaking_ka": 63, "peak_ka": 160, "thermal_ka": 63},
)

TRANSFORMERS: tuple[dict, ...] = (
    {"sn_mva": 6.3, "kv": 10, "uk": 4.5, "pk_kw": 44, "p0_kw": 7.2},
    {"sn_mva": 10, "kv": 10, "uk": 4.5, "pk_kw": 62, "p0_kw": 9.8},
    {"sn_mva": 20, "kv": 35, "uk": 8.0, "pk_kw": 95, "p0_kw": 16.2},
    {"sn_mva": 31.5, "kv": 110, "uk": 10.5, "pk_kw": 148, "p0_kw": 26.8},
    {"sn_mva": 50, "kv": 110, "uk": 10.5, "pk_kw": 210, "p0_kw": 36.6},
    {"sn_mva": 120, "kv": 220, "uk": 14.0, "pk_kw": 436, "p0_kw": 74.0},
    {"sn_mva": 240, "kv": 220, "uk": 14.0, "pk_kw": 764, "p0_kw": 122.8},
)

CONDUCTORS: tuple[dict, ...] = (
    {"model": "LGJ-120", "area_mm2": 120, "ampacity_a": 380, "r_ohm_per_km": 0.2496},
    {"model": "LGJ-150", "area_mm2": 150, "ampacity_a": 445, "r_ohm_per_km": 0.198},
    {"model": "LGJ-185", "area_mm2": 185, "ampacity_a": 515, "r_ohm_per_km": 0.1572},
    {"model": "LGJ-240", "area_mm2": 240, "ampacity_a": 610, "r_ohm_per_km": 0.1207},
    {"model": "LGJ-300", "area_mm2": 300, "ampacity_a": 690, "r_ohm_per_km": 0.0961},
    {"model": "LGJ-400", "area_mm2": 400, "ampacity_a": 835, "r_ohm_per_km": 0.0721},
    {"model": "LGJ-500", "area_mm2": 500, "ampacity_a": 960, "r_ohm_per_km": 0.0573},
    {"model": "LGJ-630", "area_mm2": 630, "ampacity_a": 1090, "r_ohm_per_km": 0.0455},
)

CABLES: tuple[dict, ...] = (
    {"model": "YJV-3x70", "area_mm2": 70, "ampacity_a": 190, "k": 142},
    {"model": "YJV-3x95", "area_mm2": 95, "ampacity_a": 230, "k": 142},
    {"model": "YJV-3x120", "area_mm2": 120, "ampacity_a": 260, "k": 142},
    {"model": "YJV-3x150", "area_mm2": 150, "ampacity_a": 300, "k": 142},
    {"model": "YJV-3x185", "area_mm2": 185, "ampacity_a": 340, "k": 142},
    {"model": "YJV-3x240", "area_mm2": 240, "ampacity_a": 400, "k": 142},
    {"model": "YJV-3x300", "area_mm2": 300, "ampacity_a": 450, "k": 142},
)

TABLES: dict[str, tuple[dict, ...]] = {
    "breakers": BREAKERS,
    "transformers": TRANSFORMERS,
    "conductors": CONDUCTORS,
    "cables": CABLES,
}


@dataclass(frozen=True)
class LookupError_(ValueError):
    """查不到满足过滤条件的记录。"""


def lookup(table: str, **filters: object) -> list[dict]:
    """按字段精确过滤。无过滤条件返回全表。"""
    if table not in TABLES:
        raise ValueError(f"未知表 {table}（可选: {', '.join(TABLES)}）")
    rows = TABLES[table]
    for key, value in filters.items():
        rows = [r for r in rows if r.get(key) == value]
    return list(rows)


def nearest_capacity(table: str, field: str, needed: float) -> dict:
    """取满足 needed 的最小记录（容量就近向上选型）。"""
    if table not in TABLES:
        raise ValueError(f"未知表 {table}")
    rows = TABLES[table]
    if field not in rows[0]:
        raise ValueError(f"表 {table} 没有字段 {field}")
    eligible = [r for r in rows if float(r[field]) >= needed]
    if not eligible:
        raise ValueError(f"{table} 中没有 {field} ≥ {needed} 的记录")
    return min(eligible, key=lambda r: float(r[field]))


def breaker_by_voltage(kv: float) -> list[dict]:
    """按电压等级查断路器（额定电压 ≥ kv 的全部记录）。"""
    rows = [r for r in BREAKERS if float(r["kv"]) >= kv]
    return sorted(rows, key=lambda r: float(r["kv"]))
