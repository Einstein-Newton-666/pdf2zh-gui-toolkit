@echo off
rem ============================================================
rem  Apply Chinese labels to the pdf2zh GUI.
rem  Run this once, and again after upgrading pdf2zh-next
rem  (an upgrade overwrites the patched files inside .venv).
rem  Keep this file ASCII-only.
rem ============================================================
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo Cannot find %PY%
    pause
    exit /b 1
)
"%PY%" "%~dp0apply-cn-labels.py"
echo.
echo Done. Restart the GUI to see Chinese labels.
pause >nul