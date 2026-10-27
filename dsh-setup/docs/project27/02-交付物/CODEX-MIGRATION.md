# Codex 技能迁移记录（用户级 DSH）

迁移日期：2026-10-26。迁移目标：`C:\Users\邓庆帅\.dsh\skills`（用户级，对所有项目生效）。
来源：`C:\Users\邓庆帅\.codex\skills`（17 个个人技能）与 `C:\Users\邓庆帅\.codex\skills\.system`（5 个系统技能）。

原则：**按目录原样复制**，保留 `references/`、`scripts/` 的相对结构，不改写原技能正文；需要宿主工具的部分只标状态，不假装已接通。

## 一、已迁移技能（22 + 1）

| 技能 | 来源 | 文件数 | 状态 |
|---|---|---|---|
| audio-transcriber | 个人 | 3 | 需本机 `faster-whisper` 等依赖 |
| bi-digital-employee | 个人 | 17 | 可用（纯文本方法 + references） |
| brainstorming | 个人 | 11 | 可用（纯文本方法） |
| design-taste-frontend | 个人（源自 `taste-skill` 目录） | 1 | 可用（纯文本方法） |
| frontend-design-codex | 个人（源自 `frontend-design` 目录） | 17 | 可用（方法可参考） |
| hatch-pet | 个人 | 30 | 依赖 Codex 宠物打包工具链，仅供参考 |
| imagegen | 系统 | 12 | 依赖 Codex 图像生成工具，仅供参考 |
| json-canvas | 个人 | 2 | 可用（纯文本方法） |
| obsidian-bases | 个人 | 2 | 可用（纯文本方法） |
| obsidian-cli | 个人 | 1 | 需本机 Obsidian CLI |
| obsidian-markdown | 个人 | 4 | 可用（纯文本方法） |
| openai-docs | 系统 | 17 | 可用（资料性，非实时） |
| pdf | 个人 | 4 | 可用（需本机 PDF 库/渲染工具） |
| playwright | 个人 | 9 | 需本机 `playwright-cli` |
| project-execution-framework | 个人 | 2 | 可用（纯文本方法） |
| ragflow-kb-ops | 个人 | 7 | 文本流程可用；连接/凭据/数据集未验证 |
| relationship-architecture-diagram | 个人 | 3 | 可用（纯文本方法） |
| review-agent | 系统 | 2 | 可用（只读评审方法） |
| sap-exam | 个人 | 5 | 可用（纯文本方法 + references） |
| skill-creator | 系统 | 9 | 可用（方法可参考） |
| skill-installer | 系统 | 8 | 原文面向 `$CODEX_HOME/skills`，安装目标需改为 DSH 目录 |
| ui-ux-pro-max | 个人 | 3 | 可用（纯文本方法） |
| obsidian-memory-read | 本次新增 | 1 | 可用（只读入口，见下） |

两处目录名与 frontmatter `name` 不一致，迁移时按 `name` 改名：`frontend-design` → `frontend-design-codex`，`taste-skill` → `design-taste-frontend`。

两处 description 原文含未加引号的 `: `（`bi-digital-employee`、`project-execution-framework`），YAML 解析会失败导致技能被静默跳过；迁移时已改为双引号包裹，正文未动。

## 二、Obsidian 读取入口

新增 `obsidian-memory-read` 技能，承载 `03-知识库读取指南.md` 的约定：先征求同意再读；唯一知识库为 `...\2026项目\codex\个人知识库-纯知识库候选`；`obsidian_knowledge` 只是引擎目录。未注册 MCP，未读取笔记正文。

## 三、Codex 插件：未迁移，需独立接入

复制技能文件不能让插件可用。`config.toml` 中启用的 14 个插件分三类：

| 插件 | 缺什么 |
|---|---|
| chrome、browser、visualize、computer-use、unified-computer-use、codex-app-tools | Codex 宿主内建能力（浏览器连接、桌面控制、会话面板）；DSH 侧需自建对应工具或 MCP，无文件可复制 |
| documents、spreadsheets、presentations、pdf、template-creator | 文档运行时与渲染链路；DSH 可用现有 office 系列技能承接，但需另行验证依赖，不能靠本目录生效 |
| github、figma、hyperframes | 远程连接、账户授权或 CLI；需单独配置与凭据，本次未触碰 |

本地 MCP：`node_repl` 属 Codex 宿主管道，未迁移；`obsidian_memory` 仅有 Python 服务代码与接口清单，DSH 未注册，不可声称已可调用。

## 四、验证与回滚

- 复制后逐目录比对文件数（169 个文件全部一致），frontmatter 名称与目录名全部一致。
- 用户级技能在本会话不热加载；新开 DSH 会话后可在技能目录看到上述技能。
- 回滚：删除 `C:\Users\邓庆帅\.dsh\skills` 下对应目录即可，Codex 原目录未被改动。

来源依据：`codex-能力与知识指南/02-插件与工具边界.md`、`03-知识库读取指南.md`、`05-DSH使用与兼容说明.md`（2026-10-26 快照）。
