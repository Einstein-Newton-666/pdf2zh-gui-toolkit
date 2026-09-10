<#
.SYNOPSIS
    本地打包发布：把本仓库生成 zip（并可选打标签推送到 GitHub）。

.DESCRIPTION
    用的是 git archive，只会收进 git 跟踪的文件 —— 天然排除 .venv / .uv-cache /
    .edge-profile / output / gui-auth.txt 这些不该发出去的东西。

.EXAMPLE
    .\打包发布.ps1                      # 只生成 dist\pdf2zh-gui-toolkit-<日期>.zip
    .\打包发布.ps1 -Tag v1.0.0          # 用指定版本号打 zip，并创建标签
    .\打包发布.ps1 -Tag v1.0.0 -Push    # 再把标签推上去（GitHub Actions 会自动发 Release）
#>
[CmdletBinding()]
param(
    [string]$Tag = ("v" + (Get-Date -Format 'yyyy.MMdd')),
    [switch]$Push
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# 工作区必须干净，否则打出来的包和标签对不上
$dirty = git status --porcelain
if ($dirty) {
    Write-Host "工作区有未提交的改动，请先 commit：" -ForegroundColor Yellow
    $dirty | ForEach-Object { Write-Host "  $_" }
    exit 1
}

$dist = Join-Path $PSScriptRoot 'dist'
New-Item -ItemType Directory -Force -Path $dist | Out-Null
$zip = Join-Path $dist ("pdf2zh-gui-toolkit-{0}.zip" -f $Tag)

Write-Host "== 打包 $Tag ==" -ForegroundColor Cyan
git archive --format=zip --prefix="pdf2zh-gui-toolkit-$Tag/" -o $zip HEAD
if ($LASTEXITCODE -ne 0) { throw "git archive 失败" }

Write-Host "`n== 包内容 ==" -ForegroundColor Cyan
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
try {
    $archive.Entries | Sort-Object FullName | ForEach-Object { "  {0,8:N0} B  {1}" -f $_.Length, $_.FullName }
    "`n  共 {0} 个文件，{1:N1} KB" -f $archive.Entries.Count, ((Get-Item $zip).Length / 1KB)
} finally { $archive.Dispose() }

Write-Host "`n产物: $zip" -ForegroundColor Green

if ($Push) {
    Write-Host "`n== 打标签并推送（会触发 GitHub Actions 自动发 Release）==" -ForegroundColor Cyan
    git tag -a $Tag -m "release $Tag"
    git push origin $Tag
    Write-Host "`n已推送标签 $Tag，稍后到 GitHub 的 Actions / Releases 页面看结果：" -ForegroundColor Green
    Write-Host "  https://github.com/Einstein-Newton-666/pdf2zh-gui-toolkit/actions"
} else {
    Write-Host "`n下一步（想发布的话）：" -ForegroundColor Yellow
    Write-Host "  .\打包发布.ps1 -Tag $Tag -Push"
    Write-Host "  或手动： git tag $Tag; git push origin $Tag"
}
