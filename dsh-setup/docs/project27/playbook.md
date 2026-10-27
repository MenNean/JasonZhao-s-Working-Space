# Playbook: DSH 能力迁移与工作台搭建

## Objective

把 Codex 侧的能力盘清楚，能迁的迁进 DSH 并验证可用，不能迁的写清缺口；在 DSH 上装一个最小可用的工作台（任务看板 + 皮肤中心），最后按 Obsidian 库的项目约定在工作区留一份可追溯的项目记录。

## Inputs and Constraints

| 项 | 内容 |
|---|---|
| 输入 | `codex-能力与知识指南/`（2026-10-26 快照）、`C:\Users\邓庆帅\.codex\skills`、`~/.dsh/profiles/desktop`、Obsidian 库的启动必读 / 个人偏好 / 项目首页样例 |
| 目标落点 | 技能：`~/.dsh/skills`；项目：工作区 `project27-DSH能力迁移与工作台搭建-20261026/` |
| 硬约束 | 不打开 Codex 凭据；Obsidian 只读约定内容，不写回、不提炼；不改 Codex 原目录 |
| 环境 | DSH 0.2.1-rc.3，desktop profile 由客户端应用内专管；PATH 无 `dsh` 命令 |
| 授权 | 技能迁移与插件安装经用户确认；Obsidian 读取经用户逐次授权 |

## Execution Steps

| # | 步骤 | 做法 | 结果 |
|---|---|---|---|
| S1 | 指南只读盘点 | 读 `00-总览/01-技能目录/02-插件边界/03-知识库/05-兼容说明` | 17 个人 + 5 系统 + 25 插件技能；14 个启用插件 |
| S2 | 环境勘察 | 列 Codex 技能目录与体积；查 `~/.dsh/skills` 是否存在、node/npx、profile 结构 | 用户级目录不存在；Node 24.14；无 `dsh` CLI |
| S3 | 暂存复制 | 22 个技能目录复制到工作区暂存，逐目录比对文件数 | 169 个文件全部一致 |
| S4 | 结构校验 | 校验 frontmatter 的 `name` 与目录名；扫描正文里的 Codex 绝对路径 | 2 处目录名与 `name` 不符 |
| S5 | 修正 | 按 `name` 改名；发现技能目录少了 2 个，定位为 description 含未加引号的 `: ` 导致 YAML 解析失败，加引号修复 | 修复后 23 个技能全部可解析 |
| S6 | 落用户级目录 | 复制到 `~/.dsh/skills`；用 `skill` 工具实测加载 `bi-digital-employee` | 热加载成功，catalog 出现 23 个用户级技能 |
| S7 | 新增 Obsidian 入口 | 写 `obsidian-memory-read` 技能：先问后读、唯一知识库路径、DSH 读取方式、边界 | 已随用户级目录加载 |
| S8 | 插件边界梳理 | 14 个插件按「文档 / 浏览器 / 桌面 / 平台 / 运行时 / 记忆」分类，写迁移记录 | 明确「插件不是迁移，是重新接入」 |
| S9 | 社区方案调研 | 查 awesome 目录、better-sidebar、dsh-web、dashboard、skills-management 的 README 与 npm 元数据 | 选定 dsh-web 最小组合而非全家桶 |
| S10 | 安装工作台 | 用户在客户端「设置 → 插件」装 `@linxin666/dsh-client-ui-task-board@0.4.8`、`@linxin666/dsh-client-ui-skin-center@0.4.8`；本鱼核对 profile 与服务 | dependencies / bundles / node_modules 三处齐全；`task_board_list` 正常 |
| S11 | 项目初始化 | 按库约定建 `00-项目首页.md`、`01-工作记录/`、`02-交付物/` | 已建，记录两份 |
| S12 | 补 playbook 与可复跑校验 | 补本文件、`project.md`、`scripts/verify_migration.ps1` 与 `output/` 日志 | 见下方验收 |
| S13 | 技能桥接方案评估 | 核查 `@dsh-skillport/bundle`（npm）、`dsh-plugin-codex-bridge`（npm/仓库）、`skills-management` 的可用性与风险 | 决定**不装**，见 `03-决策记录/2026-10-26-技能桥接方案评估.md` |

**为什么没有数据脚本**：S1–S9 以读取、比对、写文档为主，单次性动作比脚本更直接；只有"迁移是否到位"值得反复检查，所以只给 S12 写了一个校验脚本。

## Expected Outputs

```text
project27-DSH能力迁移与工作台搭建-20261026/
├─ project.md
├─ playbook.md
├─ 00-项目首页.md
├─ 01-工作记录/
│  ├─ 2026-10-26-能力盘点与技能迁移.md
│  └─ 2026-10-26-插件边界与工作台安装.md
├─ 02-交付物/
│  └─ CODEX-MIGRATION.md
├─ 03-决策记录/
│  └─ 2026-10-26-技能桥接方案评估.md
├─ scripts/
│  └─ verify_migration.ps1
└─ output/
   └─ verify_migration/
      └─ result-20261026.txt
```

## Acceptance Criteria

| # | 标准 | 判定方式 | 结果 |
|---|---|---|---|
| AC1 | 23 个技能目录、每个含 SKILL.md | `scripts/verify_migration.ps1` 清点 | 通过（10 项全过） |
| AC2 | 含特殊 description 的两个技能可被解析 | `skill` 工具实际加载 `bi-digital-employee` | 通过 |
| AC3 | 用户级技能被 DSH 热加载 | 会话技能目录出现全部 23 个 | 通过 |
| AC4 | 两个插件写入 profile 三处 | package.json dependencies + bundles + node_modules | 通过 |
| AC5 | 任务看板服务可用 | `task_board_list` 返回 ok | 通过 |
| AC6 | 项目记录可追溯 | 首页 + 记录 + 清单 + 本 playbook | 通过 |

## Status

| Field | Value |
| --- | --- |
| Current task | DSH 能力迁移与工作台搭建 |
| Playbook version | v1 |
| Execution round | 1 |
| Latest error | 两个技能因 description 含未加引号的 `: ` 被 YAML 解析跳过（已修复并复验） |
| State | VALIDATED |
