@echo off
rem ============================================================
rem  Harden: block LAN access to the GUI port, keep localhost working.
rem  Windows Firewall does not filter loopback traffic, so the GUI
rem  keeps working at http://127.0.0.1:7860 while other devices on the
rem  same network can no longer reach it. Needs administrator once.
rem ============================================================
net session >nul 2>&1
if errorlevel 1 (
    echo Requesting administrator privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$n='pdf2zh GUI - block inbound LAN'; Remove-NetFirewallRule -DisplayName $n -ErrorAction SilentlyContinue; New-NetFirewallRule -DisplayName $n -Direction Inbound -Protocol TCP -LocalPort 7860-7875 -Action Block -Profile Any | Out-Null; Write-Host ''; Write-Host 'Done. Inbound LAN access to ports 7860-7875 is now blocked.'; Write-Host 'Local use at http://127.0.0.1:7860 is unaffected.'"
echo.
echo Press any key to close...
pause >nul