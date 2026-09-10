@echo off
rem ============================================================
rem  PDF Translator GUI  -  WITH username/password login
rem  Use this one on untrusted networks (campus wifi etc.).
rem  The password is printed in this window and stored in gui-auth.txt
rem ============================================================
chcp 65001 >nul
cd /d "%~dp0"
>>"%~dp0launcher.log" echo [%date% %time%] cmd entry reached - with login
set "PS=powershell"
where pwsh >nul 2>nul && set "PS=pwsh"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0gui-launcher.ps1" %*
echo.
echo Service stopped. Press any key to close this window...
pause >nul