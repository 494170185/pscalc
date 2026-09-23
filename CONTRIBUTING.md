# 贡献指南

## 开发环境

```bash
pip install -r requirements-dev.txt
python -m pytest          # 全部测试
ruff check .              # lint
python tools/check_secrets.py   # 敏感信息扫描（必须 clean）
```

## 提交规范

- Conventional commits：`feat:` / `fix:` / `docs:` / `test:` / `refactor:` / `chore:`
- 一次提交一个主题（模块 + 对应测试 + CHANGELOG 条目）
- 不提交任何真实密钥、令牌、客户数据或内部地址

## 新增功能的工作流（TDD）

1. 先写测试（含边界与非法输入）
2. 实现模块，docstring 给出口径（引用标准条文）
3. `pytest` + `ruff` + `check_secrets` 三关全过再提交

## 设计约束

- **零第三方运行时依赖**：核心库只用标准库（pytest/ruff 仅开发期）
- **辐射网口径**：潮流与戴维南等值都假设树形拓扑，环网在加载/校验时显式拒绝
- **口径显式**：工程习惯取值（如 c 系数）不静默切换，参数显式给
- 报告是纯字符串，方便管道与版本比较

## 发布

版本号走语义化版本，记录在 CHANGELOG.md。
