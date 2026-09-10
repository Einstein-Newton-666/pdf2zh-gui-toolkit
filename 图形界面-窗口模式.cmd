@echo off
rem ============================================================
rem  PDF Translator GUI  -  Edge app window mode, NO login
rem  Keep this file ASCII-only and avoid parentheses in names.
rem ============================================================
chcp 65001 >nul
cd /d "%~dp0"
>>"%~dp0launcher.log" echo [%date% %time%] cmd entry reached - app window no-login
set "PS=powershell"
where pwsh >nul 2>nul && set "PS=pwsh"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0gui-launcher.ps1" -AppMode -NoAuth %*
echo.
echo Service stopped. Press any key to close this window...
pause >nul