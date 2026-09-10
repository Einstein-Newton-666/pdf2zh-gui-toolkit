@echo off
rem ============================================================
rem  PDF Translator (pdf2zh_next + BabelDOC, no Zotero needed)
rem  Usage 1: drag PDF file(s) or a folder onto this file
rem  Usage 2: PDFTranslate.cmd "D:\papers\a.pdf"
rem           PDFTranslate.cmd "D:\papers\inbox" deepseek sk-xxxx
rem  arg1 = pdf/folder   arg2 = service   arg3 = api key
rem
rem  Keep ASCII-only: cmd.exe reads .cmd in the console codepage
rem  (GBK on zh-CN Windows); non-ASCII here would be garbled.
rem  Chinese messages come from translate-pdf.ps1 instead.
rem ============================================================
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PS=powershell"
where pwsh >nul 2>nul && set "PS=pwsh"

if "%~1"=="" (
    echo.
    echo   Drag a PDF file or a folder onto this file to translate it.
    echo   Or run:  PDFTranslate.cmd "D:\papers\a.pdf" [service] [apiKey]
    echo   service: siliconflowfree ^(default, free^) / deepseek / siliconflow / zhipu / openai / bing / google
    echo.
    pause
    exit /b 1
)

set "SERVICE=%~2"
if "%SERVICE%"=="" set "SERVICE=siliconflowfree"

if "%~3"=="" (
    "%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0translate-pdf.ps1" -Path "%~1" -Service %SERVICE%
) else (
    "%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0translate-pdf.ps1" -Path "%~1" -Service %SERVICE% -ApiKey "%~3"
)

echo.
echo Done. Output is in the "output" folder. Press any key to close...
pause >nul
