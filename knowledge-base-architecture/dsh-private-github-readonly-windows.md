---
title: Windows版DSH只读接入GitHub私有知识库
type: method-card
scope: windows-dsh-github-readonly
created: 2026-10-27
updated: 2026-10-27
tags:
  - DSH
  - GitHub
  - SSH
  - 知识库
source_path: "session:2026-10-27-DSH-GitHub私有知识库授权"
evidence_type: 对话整理与操作方案，目标电脑尚未实测
applicable_scope: 在另一台Windows电脑上，让DeepSeek Harness读取GitHub私有Markdown知识库
publication: public
---

# Windows 版 DSH 只读接入 GitHub 私有知识库

## 目标与方案

在另一台 Windows 电脑上，通过仓库专用的只读 SSH Deploy Key 拉取私有知识库，再让 DeepSeek Harness（DSH）读取本地 Markdown 文件。

顺序为：目标电脑生成密钥 → GitHub 添加只读公钥 → 目标电脑克隆仓库 → DSH 打开本地知识库 → 需要时拉取更新。

GitHub 仓库继续保持 Private。公开这份操作说明，不会让私有仓库的内容变成公开内容。

## 授权分别解决什么

| 层级 | 解决的问题 | 说明 |
|---|---|---|
| GitHub Deploy Key | 允许目标电脑拉取指定私有仓库 | 不勾选写入权限，只授权这个仓库 |
| Windows 本地目录 | 存放克隆后的知识文件 | GitHub 只读授权不限制本地文件的编辑 |
| DSH 工作目录或目录授权 | 允许 DSH 读取本地文件 | 根据实际版本提供的目录访问能力配置 |
| DSH 使用约定 | 约定检索、引用来源及不修改文件 | 提示词是行为约定，不等同于操作系统的强制只读权限 |

本方案不依赖 GitHub MCP 或 Obsidian MCP。Deploy Key 能拉取整个仓库，不能将权限细分到其中某个文件夹。

## 1. 检查目标电脑环境

以下 PowerShell 命令均在要使用 DSH 的另一台 Windows 电脑执行。

```powershell
git --version
ssh -V
```

两条命令都应显示版本。缺少 Git 时安装 [Git for Windows](https://git-scm.com/downloads/win)。缺少 SSH 时，安装或启用 Windows 的 OpenSSH 客户端后再继续。

## 2. 在目标电脑生成专用密钥

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.ssh" | Out-Null
$dshKey = "$env:USERPROFILE\.ssh\dsh_knowledge_readonly"

if ((Test-Path -LiteralPath $dshKey) -or (Test-Path -LiteralPath "$dshKey.pub")) {
    throw "同名密钥已存在，请先确认用途；不要覆盖。需要新密钥时请改用新的文件名。"
}

ssh-keygen -t ed25519 -f $dshKey -C "dsh-knowledge-readonly"
if ($LASTEXITCODE -ne 0) { throw "密钥生成失败，请检查终端提示。" }
```

根据提示设置密钥密码。需要无人值守拉取且已妥善保护这台电脑时，可选择留空；设置密码后，使用时需要解锁私钥或配置 SSH agent。

| 文件 | 用途 |
|---|---|
| `dsh_knowledge_readonly.pub` | 公钥，添加到 GitHub |
| `dsh_knowledge_readonly` | 私钥，保留在目标电脑，不上传、不发送 |

复制公钥：

```powershell
Get-Content -LiteralPath "$dshKey.pub" | Set-Clipboard
```

## 3. 在 GitHub 添加只读 Deploy Key

由拥有仓库管理权限的账号操作：

1. 打开私有知识库仓库，进入 **Settings → Deploy keys → Add deploy key**。
2. Title 填写便于辨认的名称，例如 `Windows-DSH-readonly`。
3. Key 粘贴上一步复制的完整公钥。
4. **不要勾选 Allow write access**。
5. 点击 **Add key**。

设置页地址的格式为：`https://github.com/仓库所有者/仓库名称/settings/keys`。

只把 `.pub` 公钥交给仓库管理员；私钥始终留在目标电脑。

## 4. 克隆知识库并保存专用密钥配置

把下面两项替换成实际的仓库所有者与仓库名称。公开文档使用占位符，不包含真实私有仓库内容。

```powershell
$repoOwner = "YOUR_GITHUB_USERNAME"
$repoName = "YOUR_PRIVATE_REPOSITORY"

if ($repoOwner -eq "YOUR_GITHUB_USERNAME" -or $repoName -eq "YOUR_PRIVATE_REPOSITORY") {
    throw "请先将 repoOwner 和 repoName 替换为实际值。"
}

$dshKey = "$env:USERPROFILE\.ssh\dsh_knowledge_readonly"
$dshRepo = Join-Path "$env:USERPROFILE\Documents" $repoName
$dshSsh = 'ssh -i "' + $dshKey.Replace('\', '/') + '" -o IdentitiesOnly=yes'

if (-not (Test-Path -LiteralPath $dshKey)) { throw "未找到专用私钥。" }
if (Test-Path -LiteralPath $dshRepo) { throw "目标目录已存在，请先检查目录或另选克隆位置。" }

git -c "core.sshCommand=$dshSsh" clone "git@github.com:$repoOwner/$repoName.git" $dshRepo
if ($LASTEXITCODE -ne 0) { throw "克隆失败，请检查 SSH 授权与仓库地址。" }

git -C $dshRepo config core.sshCommand $dshSsh
if ($LASTEXITCODE -ne 0) { throw "保存仓库专用 SSH 配置失败。" }

git -C $dshRepo status --short --branch
```

第一次连接时可能要求确认 GitHub 服务器指纹。先与 [GitHub 官方 SSH 指纹](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)核对，一致后再确认。不要关闭主机指纹检查。

这里通过 Git 仓库级配置指定密钥，不修改全局 Git 或 SSH 配置，也不替换其他项目正在使用的密钥。

## 5. 让 DSH 读取本地目录

在 DSH 中打开克隆后的目录，或通过当前版本支持的方式授予该目录的读取权限。本文没有验证目标电脑的 DSH 版本及菜单名称，不预设具体按钮。

可向 DSH 提供以下工作说明，把路径替换为实际目录：

> 知识库目录为 `C:\Users\你的用户名\Documents\实际仓库名`。请先查看目录及启动说明，再按问题检索相关 Markdown 文件，回答时给出来源文件路径。知识库以只读方式使用，不修改或删除文件，不执行提交或推送。若无法读取该目录，请说明缺少的目录访问权限，不要自行扩大权限。

如果 DSH 只能读取当前工作区，就把克隆后的知识库目录作为工作目录；如果支持额外目录授权，则按实际需要授权。

GitHub 的只读 Deploy Key 限制远端写入；它不会使本地目录自动变成只读。需要强制禁止本地编辑时，应另行配置文件系统或宿主沙箱权限。

## 6. 获取后续更新

每次准备更新时，先检查本地是否有修改，再拉取。新开的 PowerShell 窗口需要重新设置实际路径：

```powershell
$dshRepo = "$env:USERPROFILE\Documents\实际仓库名"

git -C $dshRepo status --short
if ($LASTEXITCODE -ne 0) { throw "无法读取本地仓库状态。" }

$dshChanges = git -C $dshRepo status --porcelain
if ($LASTEXITCODE -ne 0) { throw "无法检查本地修改。" }
if ($dshChanges) { throw "本地存在修改，先保留并处理这些修改，再更新知识库。" }

git -C $dshRepo pull --ff-only
if ($LASTEXITCODE -ne 0) { throw "更新失败，请检查认证、网络或本地与远端的分支状态。" }
```

拉取只能获取已经推送到 GitHub 的内容。其他电脑上尚未推送的修改不会自动出现在这里。本说明不创建定时任务，也不更改已有同步计划。

## 7. 验收与常见问题

完成配置后，由目标电脑实际检查：

- 能克隆私有仓库，并找到预期的 Markdown 文件。
- GitHub 上该 Deploy Key 未勾选写入权限。
- DSH 能读取指定笔记，回答时能给出正确来源路径。
- 工作目录干净时，`git pull --ff-only` 能完成更新。

| 现象 | 优先检查 |
|---|---|
| `Permission denied (publickey)` | 公钥是否加在正确仓库；私钥路径是否正确；是否采用专用密钥配置 |
| `Repository not found` | 仓库所有者和名称是否正确；密钥是否获该仓库授权 |
| Git 能拉取，但 DSH 读不到文件 | DSH 工作目录或额外目录访问权限 |
| 克隆目录已存在 | 检查已有内容；已是同一仓库时直接检查其密钥配置并更新，不覆盖目录 |
| 拉取时分支不能快进 | 保留本地状态后排查分支差异，不自动重置或强推 |

## 8. 撤销与适用边界

撤销时，在 GitHub 仓库的 **Settings → Deploy keys** 中删除对应公钥。此后该密钥不能继续拉取仓库，已经下载到目标电脑的文件仍会保留。

公开仓库中的这份文档只提供配置方法。阅读它不代表获得私有知识库访问权，也不等于目标电脑已经完成接入。

## 来源与验证状态

- 来源：2026-10-27 关于 Windows DeepSeek Harness 访问 GitHub 私有知识库的对话；用户要求整理入库并公开此说明。
- 本文是可执行操作方案；未在另一台电脑上执行密钥生成、克隆或 DSH 阅读验证。
- GitHub 官方参考：[Deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys)、[SSH 指纹](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)。
