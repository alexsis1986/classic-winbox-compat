@echo off
setlocal
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PS%" (
  echo Windows PowerShell 5.1 was not found.
  pause
  exit /b 1
)
"%PS%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0WinBox-Toolkit.ps1" -Mode Run
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo The operation stopped. Read the error above and logs\.
pause
exit /b %RC%
