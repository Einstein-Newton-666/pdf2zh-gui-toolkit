<#
.SYNOPSIS
    批量翻译 PDF（引擎：pdf2zh_next + BabelDOC，保留公式与排版）。不需要 Zotero。

.DESCRIPTION
    本脚本只是把引擎包一层：自动定位同目录下的 .venv、把输出统一收进 output\、
    首次运行自动把 HuggingFace 资源下载切到国内镜像，并逐篇报告耗时与失败项。

.EXAMPLE
    # 1) 翻译单个文件（默认用免费服务 siliconflowfree，无需 API Key）
    .\translate-pdf.ps1 -Path "D:\论文\a.pdf"

    # 2) 翻译整个文件夹（批量）
    .\translate-pdf.ps1 -Path "D:\论文\待翻译"

    # 3) 用 DeepSeek（质量最好，作者推荐；key 只在本进程内使用，不落盘）
    .\translate-pdf.ps1 -Path "D:\论文" -Service deepseek -ApiKey "sk-xxxxxxxx"

    # 4) 先试翻前 2 页看效果，再决定要不要整篇
    .\translate-pdf.ps1 -Path ".\a.pdf" -Pages "1-2"

    # 5) 只要中文单语版，不要双语对照版
    .\translate-pdf.ps1 -Path ".\a.pdf" -NoDual
#>
[CmdletBinding()]
param(
    # PDF 文件或包含 PDF 的文件夹
    [Parameter(Mandatory = $true, Position = 0)][string]$Path,

    # 输出目录（默认脚本同目录的 output）
    [string]$Out = (Join-Path $PSScriptRoot 'output'),

    # 翻译服务：siliconflowfree=免费免key(可能漏译) / deepseek=推荐 / siliconflow、zhipu、openai、bing、google
    [ValidateSet('siliconflowfree', 'deepseek', 'siliconflow', 'zhipu', 'openai', 'bing', 'google')]
    [string]$Service = 'siliconflowfree',

    # API Key（也可用环境变量 PDF2ZH_API_KEY；命令行传入只在本进程可见）
    [string]$ApiKey = $env:PDF2ZH_API_KEY,

    # 模型名（留空用服务默认，例如 deepseek 可填 deepseek-v4-flash）
    [string]$Model = '',

    # base url（siliconflow 等需要时填，如 https://api.siliconflow.cn/v1）
    [string]$BaseUrl = '',

    # 只翻指定页，如 "1-5" 或 "1,3,7"
    [string]$Pages = '',

    [string]$LangIn = 'en',
    [string]$LangOut = 'zh',

    # 并发（免费服务限流严重时设 2 或更低；0=用引擎默认）
    [int]$Qps = 0,

    [switch]$NoAutoGlossary,   # 关闭自动术语提取（省 token）
    [switch]$NoDual,           # 不生成双语对照版
    [switch]$NoMono,           # 不生成单语版
    [switch]$SkipScannedDetection,
    # 打开引擎的 --debug（注意不能叫 -Debug：那是 PowerShell 公共参数）
    [switch]$EngineDebug
)

$ErrorActionPreference = 'Stop'

$exe = Join-Path $PSScriptRoot '.venv\Scripts\pdf2zh_next.exe'
if (-not (Test-Path $exe)) { throw "找不到翻译引擎：$exe`n请确认 .venv 与本脚本在同目录（重装见 README-install.md）" }

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$outFull = (Resolve-Path $Out).Path

# 首次运行需要下载字体与版面模型（BabelDOC 资源），国内直连 HuggingFace 常失败 → 默认走镜像
if (-not $env:HF_ENDPOINT) { $env:HF_ENDPOINT = 'https://hf-mirror.com' }

# 上游 rich 进度条在 GBK 控制台遇到生僻字符（如文件名里的 ﬂ 连字）会抛 UnicodeEncodeError
# 并让退出码变成 1（其实 PDF 已经翻译好了）。强制 UTF-8 输出即可规避。
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# ---- 收集待翻文件 ----
if (Test-Path $Path -PathType Container) {
    $files = @(Get-ChildItem $Path -Filter *.pdf -File | Where-Object { $_.DirectoryName -ne $outFull })
} else {
    $files = @(Get-Item $Path)
}
if ($files.Count -eq 0) { throw "没有找到 PDF：$Path" }

# ---- 组装引擎参数 ----
$args = @('--lang-in', $LangIn, '--lang-out', $LangOut, '--output', $outFull)
if ($Pages) { $args += @('--pages', $Pages) }
if ($Qps -gt 0) { $args += @('--qps', "$Qps") }
if ($NoAutoGlossary) { $args += '--no-auto-extract-glossary' }
if ($NoDual) { $args += '--no-dual' }
if ($NoMono) { $args += '--no-mono' }
if ($SkipScannedDetection) { $args += '--skip-scanned-detection' }
if ($EngineDebug) { $args += '--debug' }

switch ($Service) {
    'deepseek' {
        if (-not $ApiKey) { throw "deepseek 需要 API Key：-ApiKey 'sk-xxx'，或先设置环境变量 PDF2ZH_API_KEY" }
        $args += @('--deepseek', '--deepseek-api-key', $ApiKey)
        if ($Model) { $args += @('--deepseek-model', $Model) }
    }
    'siliconflowfree' { $args += '--siliconflowfree' }
    'siliconflow' {
        if (-not $ApiKey) { throw "siliconflow 需要 API Key" }
        $args += @('--siliconflow', '--siliconflow-api-key', $ApiKey)
        if ($Model) { $args += @('--siliconflow-model', $Model) }
        if ($BaseUrl) { $args += @('--siliconflow-base-url', $BaseUrl) }
    }
    'zhipu' {
        if (-not $ApiKey) { throw "zhipu 需要 API Key" }
        $args += @('--zhipu', '--zhipu-api-key', $ApiKey)
        if ($Model) { $args += @('--zhipu-model', $Model) }
    }
    'openai' {
        if (-not $ApiKey) { throw "openai 需要 API Key" }
        $args += @('--openai', '--openai-api-key', $ApiKey)
        if ($Model) { $args += @('--openai-model', $Model) }
        if ($BaseUrl) { $args += @('--openai-base-url', $BaseUrl) }
    }
    'bing' { $args += '--bing' }
    'google' { $args += '--google' }
}

# ---- 逐篇翻译 ----
Write-Host "服务：$Service   语言：$LangIn -> $LangOut   共 $($files.Count) 篇" -ForegroundColor Yellow
$i = 0; $failed = @()
foreach ($f in $files) {
    $i++
    Write-Host ""
    Write-Host ("=== [{0}/{1}] {2}" -f $i, $files.Count, $f.Name) -ForegroundColor Cyan
    $startedAt = Get-Date
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $exe $f.FullName @args
    $code = $LASTEXITCODE
    $sw.Stop()
    # 兜底：上游 rich 进度条偶发在 GBK 控制台崩溃（UnicodeEncodeError），会让退出码变 1，
    # 但 PDF 其实已经翻译输出。此时以「产物是否真的生成」为准，避免误报失败。
    $produced = @(Get-ChildItem $Out -Filter ($f.BaseName + '.*.pdf') -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $startedAt })
    if ($code -ne 0 -and $produced.Count -gt 0) {
        Write-Host ("    √ 完成（引擎退出码 {0}，但已生成 {1} 个文件，判定为成功），耗时 {2:N1}s" -f $code, $produced.Count, $sw.Elapsed.TotalSeconds) -ForegroundColor Green
    } elseif ($code -ne 0) {
        $failed += $f.Name
        Write-Host ("    × 失败（退出码 {0}），耗时 {1:N1}s" -f $code, $sw.Elapsed.TotalSeconds) -ForegroundColor Red
    } else {
        Write-Host ("    √ 完成，耗时 {0:N1}s" -f $sw.Elapsed.TotalSeconds) -ForegroundColor Green
    }
}

# ---- 结果清单 ----
Write-Host ""
Write-Host "输出目录：$outFull" -ForegroundColor Yellow
Get-ChildItem $Out -Filter *.pdf -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 20 |
    Select-Object @{n = '文件'; e = { $_.Name } }, @{n = 'MB'; e = { [math]::Round($_.Length / 1MB, 2) } }, LastWriteTime |
    Format-Table -AutoSize

if ($failed.Count) {
    Write-Host "失败 $($failed.Count) 篇：$($failed -join '; ')" -ForegroundColor Red
    exit 1
}
