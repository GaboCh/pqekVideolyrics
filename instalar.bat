@echo off
setlocal

echo.
echo ============================================================
echo   INSTALADOR AUTOMATICO - BINANCE TRADING
echo ============================================================
echo.

:: Detectar la carpeta donde esta este .bat (funciona en cualquier ruta)
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo [INFO] Carpeta del proyecto: %ROOT%
echo.

:: ---------------------------------------------
:: Verificar que Python esta instalado
:: ---------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo         Descargalo desde https://www.python.org/downloads/
    echo         Asegurate de marcar "Add Python to PATH" al instalar.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] %PYVER% detectado.
echo.

:: ---------------------------------------------
:: ENTORNO PRINCIPAL (raiz del proyecto)
:: ---------------------------------------------
echo ============================================================
echo  PASO 1/2 - Eliminando entorno principal antiguo...
echo ============================================================
if exist "%ROOT%\entorno" (
    echo [INFO] Cerrando procesos que usen el entorno principal...
    taskkill /f /im python.exe >nul 2>&1
    taskkill /f /im pythonw.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo [INFO] Borrando %ROOT%\entorno ...
    rmdir /s /q "%ROOT%\entorno"
    if exist "%ROOT%\entorno" (
        echo [ERROR] No se pudo eliminar el entorno. Cierra VSCode o terminales que lo usen y vuelve a intentar.
        pause
        exit /b 1
    )
    echo [OK] Entorno principal eliminado.
) else (
    echo [INFO] No habia entorno principal previo.
)
echo.

echo ============================================================
echo  PASO 2/2 - Creando entorno principal e instalando paquetes...
echo ============================================================
python -m venv "%ROOT%\entorno"
if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual principal.
    pause
    exit /b 1
)
echo [OK] Entorno principal creado.
echo.

echo [INFO] Instalando dependencias principales...
"%ROOT%\entorno\Scripts\python.exe" -m pip install --upgrade pip -q
"%ROOT%\entorno\Scripts\pip.exe" install -r "%ROOT%\requirements.txt"
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias principales.
    pause
    exit /b 1
)
echo [OK] Dependencias principales instaladas.
echo.

:: ---------------------------------------------
:: LISTO
:: ---------------------------------------------
echo ============================================================
echo   INSTALACION COMPLETADA CON EXITO
echo ============================================================
echo.
echo  Entorno principal : %ROOT%\entorno
echo.
echo  El proyecto esta listo para usarse en esta computadora.
echo ============================================================
echo.
pause
