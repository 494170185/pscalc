# 场景文件格式

场景是描述一个辐射网接线与运行方式的 JSON 文件。放在
`pscalc/scenarios/` 下的会被 `pscalc scenarios` 列出。

## 完整结构

```json
{
  "name": "110kV 变电站两绕组主变典型接线",
  "description": "一句话说明",
  "base": {"s_mva": 100, "kv": 115},
  "buses": [
    {"name": "G", "kv": 115, "source": {"sk_mva": 2000}},
    {"name": "110bus", "kv": 115},
    {"name": "10bus", "kv": 10.5}
  ],
  "branches": [
    {"type": "line", "from": "G", "to": "110bus", "r": 0.132, "x": 0.4, "km": 30},
    {"type": "transformer", "from": "110bus", "to": "10bus", "sn": 50, "uk": 10.5, "pk": 210}
  ],
  "loads": {"10bus": [30.0, 10.0]}
}
```

## 字段说明

### base（必需）

| 字段 | 类型 | 说明 |
|---|---|---|
| `s_mva` | number | 基准容量（MVA） |
| `kv` | number | 基准电压（kV，一般取电源侧平均额定电压） |

### buses（必需，≥1）

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | string | 母线名（全局唯一） |
| `kv` | number | 额定电压（kV） |
| `source` | object | 可选。等值电源参数 |

`source` 二选一：`sk_mva`（短路容量，MVA）或 `ikss_ka`
（起始对称短路电流，kA）。给了 `source` 的母线即电源母线
（潮流的平衡节点）。

### branches（必需，可为空数组）

两种支路类型：

**line**（线路）

| 字段 | 类型 | 说明 |
|---|---|---|
| `r` | number | 电阻（Ω/km） |
| `x` | number | 电抗（Ω/km） |
| `km` | number | 长度（km） |

**transformer**（双绕组变压器）

| 字段 | 类型 | 说明 |
|---|---|---|
| `sn` | number | 额定容量（MVA） |
| `uk` | number | 短路电压（%） |
| `pk` | number | 可选。负载损耗（kW），默认 0 |

### loads（可选）

`{母线名: [P_mw, Q_mvar]}`。没写的母线视为空载。

## 校验规则

加载时按顺序检查，任何一条不满足抛 `ScenarioError`：

1. 必需字段齐全、类型正确；
2. 支路引用的母线必须已定义；
3. 拓扑自检通过（有电源、无孤立母线、无环网）。

## 示例

三个内置场景：

- `substation_110.json` —— 110 kV 变电站（线路 + 主变 + 10 kV 负荷）
- `windfarm_35.json` —— 35 kV 风电汇集站（单母三分枝）
- `distribution_10.json` —— 10 kV 电缆配电网（三级链式）
