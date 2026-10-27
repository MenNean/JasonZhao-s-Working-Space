# DSH 初始化配置与技能库

DeepSeek Harness（DSH）的工作区配置快照：技能、插件清单、项目指南和一套可复跑的校验脚本。

## 包含什么

```text
dsh-setup/
├─ AGENTS.md                  # 工作区指令入口
├─ guides/                    # Codex 能力与知识指南（11 篇）
├─ skills/
│  ├─ user/                   # 用户级技能（23 个，复制到 ~/.dsh/skills 生效）
│  └─ workspace/              # 工作区级技能（dafeiyu、codex-capability-guide）
├─ profile/
│  ├─ package.json            # 桌面端 profile 的插件依赖与 bundles
│  └─ cordis.patch.yml        # profile 配置层
├─ scripts/
│  └─ verify_migration.ps1    # 迁移与安装校验（10 项）
└─ docs/project27/            # 这次迁移的项目记录、决策、playbook
```

## 怎么用

1. **技能**：把 `skills/user/*` 复制到 `~/.dsh/skills/`，重启或新开 DSH 会话即可加载；工作区级技能放 `<workspace>/.dsh/skills/`。
2. **插件**：桌面端在「设置 → 插件」里安装 `profile/package.json` 中列出的依赖（`@linxin666/dsh-client-ui-task-board`、`@linxin666/dsh-client-ui-skin-center`）。
3. **校验**：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_migration.ps1
   ```

   全部通过时退出码为 0。

## 环境基线

| 项 | 值 |
|---|---|
| DSH | 0.2.1-rc.3（桌面客户端，profile = `desktop`） |
| 技能目录 | 用户级 `~/.dsh/skills`；工作区级 `<workspace>/.dsh/skills` |
| 工作台插件 | 任务看板 + 皮肤中心，`^0.4.8`，要求 `dsh >= 0.2.1-rc.2` |

## 不包含什么

- 不含任何账号凭据：没有 `.credentials.yaml`、API Key、会话记录、`sessions/`、`storages/`。
- 不含 Codex 私有配置与凭据。
- `profile/cordis.patch.yml` 只保留模型与界面配置，不含密钥。

## 已知注意点

- 技能的 `SKILL.md` 若 description 含未加引号的 `: `，YAML 会解析失败且**静默跳过**，需加引号。
- 目录名与 frontmatter `name` 不一致时，按 `name` 命名目录。
- 桌面端 profile 由客户端应用内专管，外部 CLI 不宜直接改。

## 许可

各技能尽量保留原始 `LICENSE` 文件，详见 [NOTICE.md](NOTICE.md)。
