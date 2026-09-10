@echo off
rem ============================================================
rem  PDF Translator GUI  -  compact app window (smaller UI scale)
rem  Use when the interface looks too big on a high-DPI screen.
rem  Keep ASCII-only, no parentheses in file names.
rem ============================================================
chcp 65001 >nul
cd /d "%~dp0"
>>"%~dp0launcher.log" echo [%date% %time%] cmd entry reached - compact app window
set "PS=powershell"
where pwsh >nul 2>nul && set "PS=pwsh"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0gui-launcher.ps1" -AppMode -Compact -NoAuth %*
echo.
echo Service stopped. Press any key to close this window...
pause >nul