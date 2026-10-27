# DSH 读回验证

验证时间：2026-10-26 11:09（本机时间）。
工作区：DeepseekHarness；新会话标题：`只读验证 codex 能力指南`。
模型：界面显示 DeepSeek-V4.1-Flash，High。界面显示本次已完成，用时 16 秒。

## 验证请求

使用 `codex-capability-guide`，只读取本工作区指南和必要的指南技能，不打开 Obsidian 笔记、Codex 凭据，不执行联网操作或改文件；回答盘点数量、BI/SAP 原技能路径、Obsidian 读取约定和唯一库位置、插件是否已变成 DSH 可用工具，并引用指南文件名。

## 实际回答核对

| 检查项 | DSH 最终回答 | 判定 |
|---|---|---|
| 技能数 | 17 个个人 + 5 个系统 + 25 个插件技能 = 47；标明文件存在不等于可执行 | 一致 |
| 启用插件数 | 14；标明为 2026-10-26 指南快照，本次未重新扫描 | 一致 |
| BI 入口 | `C:\Users\邓庆帅\.codex\skills\bi-digital-employee\SKILL.md` | 一致 |
| SAP 入口 | `C:\Users\邓庆帅\.codex\skills\sap-exam\SKILL.md` | 一致 |
| Obsidian 约定 | 需要永久记忆的任务先询问；本任务明确授权后不重复问；指南不授予未来自动读取或写回权限 | 一致 |
| 唯一知识库 | 指向 `2026项目\codex\个人知识库-纯知识库候选`，指出 obsidian_knowledge 是引擎目录 | 一致 |
| 插件状态 | 已盘点，未批量安装到 DSH；Codex enabled 不代表 DSH 已接通；Obsidian MCP 尚未注册到 DSH | 一致 |
| 来源引用 | 引用了 00、01、02、03、05 指南文件 | 通过 |

## 证据与范围

以上依据 DSH 原生界面可见的最终回答核对。DSH 自述读取了总览及 01、02、03、05，未读知识笔记、凭据、未联网或改文件；本记录未另行审计 DSH 全部底层文件访问或网络日志。请求中的“不联网”指不额外进行检索或网络工具调用，DSH 模型服务仍按其已有配置运行。

该结果验证新会话能定位并使用同步指南、准确复述关键入口和边界；未单独证明原始 BI/SAP 外部路径已在 DSH 获准读取，也未证明所有技能、插件或 MCP 可执行。未单独审计启动时 AGENTS 与技能目录的每一步自动加载；本次请求显式提到了指南技能。

## 其他完成的检查

- 新指南技能通过 skill-creator 的 `quick_validate.py`：`Skill is valid!`。默认和随附 Python 缺少 PyYAML，因此把校验依赖安装到本任务 `work/validation-deps`，仅为该校验进程设置 PYTHONPATH，未修改系统 Python 环境。
- JSON 解析、Markdown 相对链接、指南 skill 入口链接检查通过。
- 输出与 DSH 副本逐文件 SHA-256 一致；具体哈希见同步清单。
- 未做远程 RAGFlow、Figma、GitHub 或 Obsidian MCP 连通测试，也未逐一执行 47 个技能。
