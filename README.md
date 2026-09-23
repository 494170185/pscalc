# pscalc —— 变电站一次设计计算库

纯 Python（零第三方依赖）的变电站/配电网一次设计计算工具：

- **短路电流**（IEC 60909 等效电压源法）：三相 Ik''/ip/ib/Ith/Sk，单相接地、两相短路
- **辐射网潮流**：前推回代法，电压分布与网损
- **无功补偿**：电容器组选型、功率因数改善
- **设备校验**：断路器（开断/动稳定/热稳定）、母线、电缆、架空线
- **计算书生成**：Markdown 报告，一键输出
- **场景库**：JSON 描述典型接线，加载即算

## 安装与运行

```bash
pip install -e .            # 安装（含 pscalc 命令）
pscalc scenarios            # 列出内置场景
pscalc run substation_110   # 跑场景，打印计算书
pscalc run windfarm_35 -o report.md
```

开发环境（pytest + ruff）：

```bash
pip install -r requirements-dev.txt
python -m pytest
ruff check .
```

## 库结构

| 模块 | 内容 | 对应里程碑 |
|---|---|---|
| `pscalc.perunit` | 标幺值体系、电压调整系数 c、峰值系数 κ | M1 |
| `pscalc.elements` | 线路/变压器/电源/负荷阻抗模型 | M2 |
| `pscalc.network` | 母线/支路拓扑、戴维南等值阻抗、环网检测 | M3 |
| `pscalc.loadmodel` | 恒功率负荷、同时率、日负荷曲线 | M4 |
| `pscalc.shortcircuit` | 三相短路全链路（Ik''/ip/ib/Ith/Sk） | M5 |
| `pscalc.unbalanced` | 单相接地、两相短路（对称分量） | M6 |
| `pscalc.correction` | IEC 60909 KT（分接）/KG（发电机）校正 | M7 |
| `pscalc.powerflow` | 前推回代潮流 | M8 |
| `pscalc.voltagedrop` | 电压损耗分解与调压建议 | M9 |
| `pscalc.compensation` | 电容器组选型与补偿效果 | M10 |
| `pscalc.equipment` | 设备校验 | M11 |
| `pscalc.report` | Markdown 计算书 | M12 |
| `pscalc.scenarios` | JSON 场景库（三个内置案例） | M13 |
| `pscalc.cli` | 命令行 | M14 |

## 场景文件格式

见 [docs/scenario-format.md](docs/scenario-format.md)。内置三个场景：
110 kV 变电站、35 kV 风电汇集站、10 kV 电缆配电网。

## 口径说明

- 短路计算基于 IEC 60909-0（等效电压源法）；c 系数按国内工程习惯取值
  （35 kV 及以下 1.05、110 kV 及以上 1.1）
- 潮流为辐射网（树形拓扑）专用；环网会在加载时被拒绝
- 全部计算在标幺值空间进行，报告按故障母线电压等级折算实际值

## License

MIT
