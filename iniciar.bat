@echo off
chcp 65001 >nul
setlocal

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "PYTHON=%ROOT%\entorno\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [ERROR] No se encontro el entorno virtual.
    echo         Ejecuta primero: instalar.bat
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   GUI - BINANCE TRADING
echo ============================================================
echo.
"%PYTHON%" "%ROOT%\main.py"
pause
