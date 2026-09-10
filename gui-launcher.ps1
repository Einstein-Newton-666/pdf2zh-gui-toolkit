<#
.SYNOPSIS
    启动 pdf2zh 的图形界面（引擎自带的 Gradio WebUI）。

.DESCRIPTION
    由同目录的 图形界面*.cmd 或桌面快捷方式调用。
    每一步都会写进同目录的 launcher.log，出问题时把那个文件发我即可定位。

    注意：本文件必须保存为「UTF-8 带 BOM」，否则 Windows PowerShell 5.1 会按 GBK
    解码导致中文乱码 + 语法错误。

.EXAMPLE
    .\gui-launcher.ps1                 # 带登录，自动开浏览器
    .\gui-launcher.ps1 -NoAuth         # 本机免登录
    .\gui-launcher.ps1 -AppMode        # 用 Edge 应用模式打开（像原生桌面软件）
    .\gui-launcher.ps1 -Port 8000      # 指定起始端口
#>
[CmdletBinding()]
param(
    [int]$Port = 7860,
    [switch]$NoAuth,
    [switch]$AppMode,
    # 紧凑模式：配合 -AppMode 使用，把界面整体缩小（高分屏/觉得界面太大时用）
    [switch]$Compact
)

$script:LogFile = Join-Path $PSScriptRoot 'launcher.log'
function Write-Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    try { Add-Content -LiteralPath $script:LogFile -Value $line -Encoding utf8 } catch { }
}
Write-Log ("=== launcher start | pid={0} | PowerShell {1} | 参数: Port={2} NoAuth={3} AppMode={4} Compact={5}" -f $PID, $PSVersionTable.PSVersion, $Port, [bool]$NoAuth, [bool]$AppMode, [bool]$Compact)

$ErrorActionPreference = 'Stop'

# 控制台编码：既修中文显示，也避免上游 rich 在 GBK 控制台抛 UnicodeEncodeError
try { chcp 65001 | Out-Null } catch { }
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch { }
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
if (-not $env:HF_ENDPOINT) { $env:HF_ENDPOINT = 'https://hf-mirror.com' }
# 代理防御：Gradio 启动时用 httpx 自检 http://127.0.0.1:<port>，
# 而 httpx 只认 NO_PROXY 环境变量、不认 Windows 的"绕过代理"名单。
# 显式声明本机不走代理，避免"自检失败 → 报 proxy software 错"。
$env:NO_PROXY = '127.0.0.1,localhost,::1'
$env:no_proxy = '127.0.0.1,localhost,::1'

$root = $PSScriptRoot
$exe = Join-Path $root '.venv\Scripts\pdf2zh_next.exe'
if (-not (Test-Path $exe)) {
    Write-Log "ERROR: 找不到引擎 $exe"
    throw "找不到翻译引擎：$exe（请确认 .venv 与本脚本同目录）"
}
Write-Log "引擎: $exe"

# ---- 挑空闲端口（用真实 bind 试探，比只看监听列表更可靠）----
function Test-PortFree([int]$p) {
    if (Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue) { return $false }
    try {
        $l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $p)
        $l.Start(); $l.Stop(); return $true
    } catch { return $false }
}
$chosen = $null
for ($p = $Port; $p -le ($Port + 10); $p++) { if (Test-PortFree $p) { $chosen = $p; break } }
if ($null -eq $chosen) { Write-Log "ERROR: 端口 $Port..$($Port+10) 全被占用"; throw "端口 $Port 起连续 11 个都在被占用，请用 -Port 指定别的起始端口" }
if ($chosen -ne $Port) { Write-Host "提示：$Port 被占用，已自动改用 $chosen" -ForegroundColor Yellow }
Write-Log "选用端口: $chosen"

# ---- 登录保护 ----
$authArgs = @()
$authFile = Join-Path $root 'gui-auth.txt'
if (-not $NoAuth) {
    if (-not (Test-Path $authFile)) {
        $chars = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'.ToCharArray()
        $pwd = -join (1..12 | ForEach-Object { $chars | Get-Random })
        Set-Content -LiteralPath $authFile -Value "pdf2zh,$pwd" -Encoding ascii
        Write-Host "已生成登录文件：$authFile（用户名 pdf2zh）" -ForegroundColor Yellow
        Write-Log "已生成登录文件 gui-auth.txt"
    }
    $authArgs = @('--auth-file', $authFile)
}
Write-Log ("认证模式: {0}" -f $(if ($NoAuth) { '免登录' } else { '用户名密码' }))

$url = "http://127.0.0.1:$chosen"
$engineArgs = @('--gui', '--server-port', "$chosen", '--ui-lang', 'zh') + $authArgs

Write-Host ""
Write-Host "==================== PDF 翻译 图形界面 ====================" -ForegroundColor Cyan
Write-Host "  地址：$url"
if (-not $NoAuth) {
    $line = (Get-Content -LiteralPath $authFile -TotalCount 1)
    $user = ($line -split ',')[0]; $pass = ($line -split ',')[1]
    Write-Host "  登录：用户名 $user    密码 $pass" -ForegroundColor Green
    Write-Host "  （密码存在 gui-auth.txt，可自行修改；改了要重启本界面才生效）"
} else {
    Write-Host "  登录：已关闭（本机免登录模式）" -ForegroundColor Yellow
    Write-Host "  [!] 上游把服务绑定在 0.0.0.0，同网段的人也能访问，务必只在可信网络使用"
}
Write-Host "  首次启动需要 10~30 秒，浏览器会自动打开，请稍等..."
Write-Host "  [!] 如果浏览器没有自动打开，请手动把上面的地址复制到浏览器打开" -ForegroundColor Yellow
Write-Host "  觉得界面太大：按 Ctrl 和减号 可以缩小（浏览器会记住）"
Write-Host "  翻译设置（含 API Key）会保存在 $env:USERPROFILE\.config\pdf2zh\ 里，填一次就记住"
Write-Host "  双语对照 PDF 默认就是「左右并排」，界面上不用额外选"
Write-Host "  [!] 这个窗口不要关，关掉就等于停止服务；翻译中途关掉会中断任务"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Log ("启动命令: {0} {1}" -f $exe, ($engineArgs -join ' '))

if ($AppMode) {
    # 应用窗口模式由我们自己开浏览器，屏掉引擎再弹一个默认浏览器（BROWSER=none 让 webbrowser 找不到浏览器）
    $env:BROWSER = 'none'
    # 后台起引擎 → 等端口就绪 → 用 Edge 应用模式打开（没有地址栏，像桌面软件）
    $proc = Start-Process -FilePath $exe -ArgumentList $engineArgs -PassThru -NoNewWindow
    Write-Log "AppMode: 引擎已后台启动 pid=$($proc.Id)"
    $ready = $false
    for ($i = 0; $i -lt 90; $i++) {
        Start-Sleep -Seconds 1
        try { $null = Invoke-WebRequest -Uri $url -TimeoutSec 2 -UseBasicParsing; $ready = $true; break } catch { }
        if ($proc.HasExited) { break }
    }
    if ($ready) {
        Write-Log "AppMode: 界面就绪，准备打开窗口"
        $edge = @(
            "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
            "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
        ) | Where-Object { Test-Path $_ } | Select-Object -First 1
        $edgeArgs = @("--app=$url")
        if ($Compact) {
            # 紧凑模式：独立配置目录 + 缩放 0.8。
            # 必须用独立 profile：Edge 已在运行时新命令只是把 URL 转交给现有进程，
            # --force-device-scale-factor 这类启动参数会被忽略。
            $profileDir = Join-Path $root '.edge-profile'
            $edgeArgs += @(
                "--user-data-dir=$profileDir",
                '--no-first-run',
                '--no-default-browser-check',
                '--force-device-scale-factor=0.8',
                '--window-size=1500,950'
            )
            Write-Log "AppMode: 紧凑模式（独立 profile + scale=0.8 + 1500x950）"
        }
        if ($edge) { Start-Process -FilePath $edge -ArgumentList $edgeArgs }
        else { Start-Process $url }
    } else {
        Write-Log "AppMode: 等待就绪超时"
        Write-Host "等待界面就绪超时，请手动在浏览器打开 $url" -ForegroundColor Yellow
    }
    Wait-Process -Id $proc.Id
    Write-Log "AppMode: 引擎进程已退出"
} else {
    # 前台运行，同时把引擎的完整输出落盘到 engine.log（排查用；也保留 rich 的控制台输出）
    $engineLog = Join-Path $root 'engine.log'
    try { Remove-Item $engineLog -Force -ErrorAction SilentlyContinue } catch { }
    & $exe @engineArgs 2>&1 | Tee-Object -FilePath $engineLog
    $code = $LASTEXITCODE
    Write-Log "前台引擎已退出，退出码=$code"
    if ($code -ne 0) {
        Write-Host ""
        Write-Host "  [!] 界面进程异常退出（退出码 $code）。完整输出已存到 engine.log" -ForegroundColor Red
        Write-Host "      常见原因：端口被占 / 安全软件拦端口 / 代理干扰本机自检" -ForegroundColor Yellow
        try {
            Get-Content $engineLog -Encoding utf8 -ErrorAction SilentlyContinue |
                Where-Object { $_ -match 'Error launching|Unavailable Invalid|Address already in use|10048|share|proxy' } |
                Select-Object -First 6 | ForEach-Object { Write-Host ("      | " + $_.Trim()) -ForegroundColor DarkYellow }
        } catch { }
    }
}
Write-Log "=== launcher end"
