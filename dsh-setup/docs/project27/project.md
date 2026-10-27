# 项目框架：DSH 能力迁移与工作台搭建

本文件是稳定的项目框架定义，不随单次任务改写；单次任务计划见 `playbook.md`。

## 目的

把外部 Codex 能力按「能用 / 需接入 / 不可迁」三类落位，并在 DSH 上维持一个最小可用的工作台，过程可追溯、可复验、可回滚。

## 目录约定

```text
project27-DSH能力迁移与工作台搭建-20261026/
├─ project.md      # 本文件：框架定义
├─ playbook.md     # 单次任务计划与执行记录（可覆盖）
├─ 00-项目首页.md   # 按 Obsidian 库的项目首页格式
├─ 01-工作记录/     # 按日期的事实记录，只追加不改写
├─ 02-交付物/       # 对外可交付的清单、文档
├─ scripts/        # 可复跑的校验脚本，按任务命名
└─ output/         # 脚本产物与日志，按任务分目录
```

## 工作方式

1. 新任务先写 `playbook.md`：目标、输入、步骤、产出、验收、状态。
2. 有可复跑价值的检查才写脚本，放 `scripts/`，产物落 `output/<task>/`。
3. 每步做完对照验收标准；不通过就回到对应步骤，不跳步。
4. 事实记录进 `01-工作记录/`，只追加；结论变化在首页状态表里更新。
5. 交付时说明产出路径、做了什么校验、还剩什么风险。

## 边界

- 不写 Obsidian 知识库（除非单独授权）；不碰凭据；不改 Codex 原目录。
- 插件安装走客户端应用内，外部脚本只做校验，不改 profile。
- 迁移以「可被 DSH 实际加载」为准，不以复制完成为准。

## 复验入口

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_migration.ps1
# 结果写入 output/verify_migration/result-<yyyyMMdd>.txt，全部通过时退出码 0
```
