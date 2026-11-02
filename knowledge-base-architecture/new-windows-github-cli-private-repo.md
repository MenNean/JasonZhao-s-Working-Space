# 新 Windows 电脑通过 GitHub CLI 访问私有知识库

整理日期：2026-11-02。

## 目标与访问链路

在新 Windows 电脑安装 Git 和 GitHub CLI（`gh`），登录有仓库权限的 GitHub 账号，再通过 API 查询或把私有知识库克隆到本地，供 Codex、DeepSeek Harness（DSH）检索使用。

```text
新电脑安装 Git / GitHub CLI
        ↓
通过浏览器登录 GitHub 并完成 CLI 授权
        ↓
GitHub 按账号已有权限决定能访问哪些仓库
        ↓
gh 查看仓库 / 调用 API / 克隆私有知识库
        ↓
Codex 或 DSH 执行 gh 命令，或读取本地 Markdown
        ↓
需要更新时 git pull --ff-only
```

GitHub 账号登录、仓库访问权与 Agent 的本地工具权限分别生效。安装 CLI 不等于获得私有仓库权限；登录后，账号仍需是仓库所有者或已获授权的成员。

本流程不会更改仓库可见性。公开这份说明也不会公开私有知识库内容。

## 一、准备条件

- Windows 电脑可以访问 GitHub，且有可用浏览器。
- 拥有 GitHub 账号，以及目标私有仓库的访问权限。
- 如果使用另一个账号，先由仓库管理员邀请，并登录该账号接受邀请。
- 选定知识库存放目录。本文示例为 `D:\AIWorkspace\knowledge-base`，可按实际磁盘修改。

本文用 `YOUR_OWNER/YOUR_PRIVATE_REPOSITORY` 表示仓库地址，请替换为自己的仓库，不要直接复制占位符执行。

## 二、安装 Git 和 GitHub CLI

在新电脑 PowerShell 执行：

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
```

安装程序可能要求确认许可或系统授权。完成后关闭并重新打开 PowerShell，检查：

```powershell
git --version
gh --version
```

两条命令都能输出版本即可。已经安装时无需重复安装。

如果无法使用 `winget`，可分别通过 [Git for Windows](https://git-scm.com/downloads/win) 和 [GitHub CLI](https://cli.github.com/) 的官方安装方式安装。

## 三、通过浏览器登录 GitHub

执行：

```powershell
gh auth login
```

按提示选择：

| 提示 | 建议选择 |
|---|---|
| GitHub 服务 | `GitHub.com` |
| Git 协议 | `HTTPS` |
| 是否让 Git 使用 GitHub 凭据（如出现） | `Yes` |
| 登录方式 | `Login with a web browser` |

终端显示一次性验证码后，按提示打开浏览器，核对登录账号，输入验证码并完成授权。菜单和提示顺序可能随版本变化，以实际界面为准。

登录完成后检查：

```powershell
gh auth status --hostname github.com
```

确认账号正确。若 Git 后续拉取仍要求登录，可执行：

```powershell
gh auth setup-git
```

这会配置 Git 使用 GitHub CLI 的凭据辅助机制。授权凭据由 CLI 在本机管理，具体存储方式以实际系统和 CLI 提示为准；不要把凭据文件、Token 或一次性验证码复制进知识库。

## 四、检查私有仓库权限

在 PowerShell 填入实际仓库所有者和名称：

```powershell
$repoOwner = 'YOUR_OWNER'
$repoName = 'YOUR_PRIVATE_REPOSITORY'

if ($repoOwner -eq 'YOUR_OWNER' -or $repoName -eq 'YOUR_PRIVATE_REPOSITORY') {
    throw '请先替换仓库所有者和仓库名称。'
}

$repoFullName = "$repoOwner/$repoName"
gh repo view $repoFullName --json nameWithOwner,visibility,isPrivate
if ($LASTEXITCODE -ne 0) { throw '仓库读取失败，请检查账号、仓库地址与访问权限。' }
```

私有仓库正常返回时，应看到 `visibility` 为 `PRIVATE`、`isPrivate` 为 `true`。这证明当前账号能读取仓库元信息，不等于已经验证写入权限。

如果看到 `404` 或 `Repository not found`，依次检查账号、仓库拼写、协作者邀请是否接受，以及组织是否要求额外的 SSO 授权。

## 五、克隆知识库到本地

接着在同一个 PowerShell 窗口执行。新窗口需要重新设置上一步的仓库变量。

```powershell
$workspaceRoot = 'D:\AIWorkspace'
$localKnowledge = Join-Path $workspaceRoot 'knowledge-base'

New-Item -ItemType Directory -Force $workspaceRoot | Out-Null
if (Test-Path -LiteralPath $localKnowledge) {
    throw '目标目录已存在，请先检查其中内容，不覆盖已有目录。'
}

# 显式使用 HTTPS，与前面的登录方式一致。
$repoHttpsUrl = "https://github.com/$repoFullName.git"
gh repo clone $repoHttpsUrl $localKnowledge
if ($LASTEXITCODE -ne 0) { throw '克隆失败，请检查网络、仓库权限和Git凭据配置。' }

git -C $localKnowledge status --short --branch
```

首次拉取会下载仓库内容，不会替目标电脑自动安装其中引用的运行环境、插件或模型。

## 六、交给 Codex 或 DSH 使用

安装后重新打开 Codex 或 DSH，确保应用能发现更新后的 PATH。若应用运行在不同的 Windows 用户、WSL、容器或远程主机中，需要在其实际执行环境单独检查 `gh` 和登录状态，不能假定继承了当前 PowerShell 的身份。

可以提供下面的工作说明，把路径和仓库替换为实际值：

> 这台电脑已安装并登录 GitHub CLI。请先执行 `gh auth status` 确认登录账号，再检查目标私有仓库的访问权限。知识库已经克隆到 `D:\AIWorkspace\knowledge-base`。请按需检索本地 Markdown，并在回答中注明来源文件路径。先按知识库自身的启动规则工作；不提交、不推送、不修改仓库可见性，也不把凭据输出到聊天或文件。如缺少目录读取或命令执行权限，请说明具体缺少什么。

Agent 有两种使用方式：

| 方式 | 适用情况 | 需要什么 |
|---|---|---|
| 运行 `gh` 查询仓库或调用 GitHub API | 检查远端文件、仓库信息等 | CLI 已登录，Agent 能执行本机命令且有网络访问权限 |
| 读取本地克隆的 Markdown | 日常知识检索与引用 | Agent 能读取该目录；需要最新内容时另行拉取 |

这条链路使用 GitHub CLI，不要求安装 GitHub MCP。仅完成 CLI 登录，也不会自动给 Agent 开放本地文件系统和命令执行能力。

## 七、获取最新知识库

每次需要更新时，先检查本地修改，再拉取：

```powershell
$localKnowledge = 'D:\AIWorkspace\knowledge-base'

git -C $localKnowledge status --short
if ($LASTEXITCODE -ne 0) { throw '无法读取本地仓库状态。' }

$localChanges = git -C $localKnowledge status --porcelain
if ($LASTEXITCODE -ne 0) { throw '无法检查本地修改。' }
if ($localChanges) {
    throw '本地存在修改或未跟踪文件，先保留并处理这些内容，再更新。'
}

git -C $localKnowledge pull --ff-only
if ($LASTEXITCODE -ne 0) { throw '拉取失败，请检查网络、认证或分支差异。' }
```

只会获得已经推送到远端的内容。其他电脑未推送的修改不在其中。本文不创建定时拉取或推送任务。

## 八、账号授权与只读 Deploy Key 如何选择

| 方式 | 授权范围 | 适合场景 |
|---|---|---|
| 本文的 GitHub CLI 账号登录 | 取决于账号、CLI 授权范围与组织策略，可能涉及多个仓库及写入操作 | 本人完整工作电脑 |
| 仓库专用只读 SSH Deploy Key | 读取指定仓库，添加公钥时不勾选写入权限 | 只给某个工具或固定设备拉取一个知识库 |

提示词中的“不推送”只是行为约定，不会把账号权限变成技术上的只读。如果希望限制到单仓库只读，可使用 [Windows 版 DSH 只读接入说明](dsh-private-github-readonly-windows.md)。

GitHub 只读授权同样不会阻止本地文件被编辑。本地强制只读应由文件系统或宿主权限另行控制。

## 九、常见问题与验收

| 现象 | 检查方法 |
|---|---|
| 找不到 `gh` 或 `git` | 重新打开终端和 Agent 应用，检查 PATH 与安装是否完成 |
| 浏览器登录的是错误账号 | 先确认浏览器账号；多个已登录 CLI 账号可按 `gh auth switch --help` 切换 |
| 能登录，不能访问私有库 | 检查账号权限、邀请接受状态及组织 SSO 要求 |
| 仓库能查看但克隆失败 | 检查 Git 安装、HTTPS 凭据辅助配置、网络与目标目录 |
| 终端成功，Agent 失败 | 检查实际 Windows 用户、WSL/容器环境、PATH、网络和工具权限 |
| Agent 读到旧内容 | 核对读取目录，并执行成功的拉取更新 |
| 拉取不能快进 | 保留当前状态，排查分支差异；不要自动 reset 或强推 |

验收应至少完成：CLI 登录正确、私有仓库查询成功、克隆成功、Agent 能引用一篇笔记的来源、工作目录干净时拉取成功。

## 十、撤销授权

在这台电脑停止使用 CLI 授权时，可以执行：

```powershell
gh auth logout --hostname github.com
```

如需撤销浏览器登录流程授予 GitHub CLI 的访问权，可在 GitHub 账号 **Settings → Applications → Authorized OAuth Apps** 中检查并撤销相应授权；撤销影响范围以 GitHub 显示为准，可能影响同一授权的其他使用场景。

退出或撤销认证后，已经克隆的文件仍在本地，其他独立配置的 SSH 密钥或凭据也不会因此自动删除。

## 验证范围与参考

本文由已讨论的操作链路整理，未在目标新电脑完成安装、登录和 Agent 读取实测。终端提示、授权菜单和 Agent 工具能力随版本及账号环境变化。

- [GitHub CLI 登录说明](https://cli.github.com/manual/gh_auth_login)
- [GitHub CLI Git 凭据配置](https://cli.github.com/manual/gh_auth_setup-git)
- [GitHub CLI 克隆仓库](https://cli.github.com/manual/gh_repo_clone)
- [GitHub CLI 检查认证](https://cli.github.com/manual/gh_auth_status)
