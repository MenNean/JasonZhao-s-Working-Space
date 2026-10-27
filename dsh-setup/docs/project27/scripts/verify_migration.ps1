#requires -Version 5.1
<#
  校验 DSH 能力迁移与工作台安装是否仍然成立。
  只读：不改 profile、不改技能目录，仅生成日志。
  用法：pwsh -File scripts/verify_migration.ps1 [-OutFile <path>]
#>
param([string]$OutFile)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutFile) {
    $OutFile = Join-Path $projectRoot ('output\verify_migration\result-' + (Get-Date -Format 'yyyyMMdd') + '.txt')
}
New-Item -ItemType Directory -Path (Split-Path -Parent $OutFile) -Force | Out-Null

$skillRoot = Join-Path $env:USERPROFILE '.dsh\skills'
$profileRoot = Join-Path $env:USERPROFILE '.dsh\profiles\desktop'
$expectedSkills = @('bi-digital-employee', 'project-execution-framework', 'sap-exam', 'obsidian-memory-read', 'skill-installer')
$plugins = @('@linxin666/dsh-client-ui-task-board', '@linxin666/dsh-client-ui-skin-center')

$checks = [System.Collections.Generic.List[object]]::new()
function Add-Check([string]$Name, [bool]$Ok, [string]$Detail) {
    $checks.Add([pscustomobject]@{ Ok = $Ok; Check = $Name; Detail = $Detail })
}

# 1. 技能目录
$dirs = @(Get-ChildItem -LiteralPath $skillRoot -Directory -ErrorAction SilentlyContinue)
Add-Check '技能目录存在' ($dirs.Count -gt 0) "$($dirs.Count) 个目录 @ $skillRoot"

$noSkill = @($dirs | Where-Object { -not (Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md')) })
Add-Check '每个目录都有 SKILL.md' ($noSkill.Count -eq 0) "缺失：$(if ($noSkill.Count -eq 0) { '无' } else { ($noSkill.Name -join ', ') })"

$missingExpected = @($expectedSkills | Where-Object { -not (Test-Path -LiteralPath (Join-Path $skillRoot (Join-Path $_ 'SKILL.md'))) })
Add-Check '关键技能齐全' ($missingExpected.Count -eq 0) "缺失：$(if ($missingExpected.Count -eq 0) { '无' } else { ($missingExpected -join ', ') })"

# 2. 曾被 YAML 卡住的两个技能
$yamlBroken = @()
foreach ($n in 'bi-digital-employee', 'project-execution-framework') {
    $line = Get-Content -LiteralPath (Join-Path $skillRoot "$n\SKILL.md") -TotalCount 4 -Encoding UTF8 |
        Where-Object { $_ -match '^description:' } | Select-Object -First 1
    if ($line -notmatch '^description:\s*"') { $yamlBroken += $n }
}
Add-Check 'description 已加引号（YAML 可解析）' ($yamlBroken.Count -eq 0) "问题项：$(if ($yamlBroken.Count -eq 0) { '无' } else { ($yamlBroken -join ', ') })"

# 3. profile 安装状态
$pkgPath = Join-Path $profileRoot 'package.json'
$pkg = if (Test-Path -LiteralPath $pkgPath) { Get-Content -LiteralPath $pkgPath -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }
$deps = if ($pkg) { @($pkg.dependencies.PSObject.Properties.Name) } else { @() }
$bundles = if ($pkg) { @($pkg.dsh.profile.bundles) } else { @() }

foreach ($p in $plugins) {
    Add-Check "依赖：$p" ($deps -contains $p) $(if ($deps -contains $p) { '已写入 dependencies' } else { '未写入' })
    Add-Check "挂载：$p" ($bundles -contains $p) $(if ($bundles -contains $p) { '已写入 bundles' } else { '未写入' })
    $nm = Join-Path $profileRoot ('node_modules\' + $p.Replace('/', '\'))
    Add-Check "实体：$p" (Test-Path -LiteralPath $nm) $(if (Test-Path -LiteralPath $nm) { 'node_modules 存在' } else { 'node_modules 缺失' })
}

# 4. 输出
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$header = @("# 迁移校验 $stamp", "# 主机：$env:COMPUTERNAME", "")
$body = $checks | ForEach-Object {
    ('{0}  {1}  {2}' -f $(if ($_.Ok) { 'PASS' } else { 'FAIL' }), $_.Check, $_.Detail)
}
$failed = @($checks | Where-Object { -not $_.Ok })
$footer = @('', ('总计 {0} 项，通过 {1}，失败 {2}' -f $checks.Count, ($checks.Count - $failed.Count), $failed.Count))
$content = @($header) + $body + $footer
$content | ForEach-Object { Write-Host $_ }
$content | Set-Content -LiteralPath $OutFile -Encoding UTF8
Write-Host "日志：$OutFile"

if ($failed.Count -gt 0) { exit 1 } else { exit 0 }

