@echo off
setlocal EnableExtensions
title Overlay Launcher

set "MAIN_SCRIPT=main.py"
set "VENV_DIR=.venv"
set "REQ_FILE=requirements.txt"
set "VER_CHECK=import sys; sys.exit(0 if (3,12) <= sys.version_info[:2] <= (3,13) else 1)"

set "BAR1=[####----------------]"
set "BAR2=[########------------]"
set "BAR3=[############--------]"
set "BAR4=[################----]"
set "BAR5=[####################]"

cd /d "%~dp0"

echo ========================================
echo   Overlay Launcher - by Xander
echo ========================================

call :step 1 "Checking Python 3.12 / 3.13"
set "PY_CMD="

py -3.13 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3.13"
    goto :python_found
)

py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3.12"
    goto :python_found
)

python -c "%VER_CHECK%" >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    goto :python_found
)

echo   [X] Python 3.12 or 3.13 was not found.
echo.
echo   This program only supports Python 3.12 and 3.13.
echo   Download Python 3.13 from https://www.python.org/downloads/
echo   During setup, tick "Add Python to PATH", then run this file again.
echo.
pause
exit /b 1

:python_found
for /f "delims=" %%v in ('%PY_CMD% --version') do set "PY_VER=%%v"
echo   [OK] Compatible Python installed - %PY_VER%

call :step 2 "Checking virtual environment"
if not exist "%VENV_DIR%\Scripts\python.exe" goto :create_venv

"%VENV_DIR%\Scripts\python.exe" -c "%VER_CHECK%" >nul 2>&1
if not errorlevel 1 goto :venv_present

echo   [!] Existing venv uses an unsupported Python version, rebuilding it...
rmdir /s /q "%VENV_DIR%"
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo   [X] Could not delete "%VENV_DIR%". Close any program using it and try again.
    pause
    exit /b 1
)
goto :create_venv

:venv_present
echo   [OK] Virtual environment present - %VENV_DIR%
goto :venv_ready

:create_venv
echo   [..] Creating "%VENV_DIR%" with %PY_VER%...
%PY_CMD% -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo   [X] Failed to create the virtual environment.
    pause
    exit /b 1
)
echo   [OK] Virtual environment created

:venv_ready

call :step 3 "Activating virtual environment"
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo   [X] Failed to activate the virtual environment.
    pause
    exit /b 1
)
echo   [OK] Virtual environment activated

call :step 4 "Checking requirements"
if not exist "%REQ_FILE%" (
    echo   [--] %REQ_FILE% not found, skipping
    goto :reqs_done
)

echo   [..] Verifying packages, installing any that are missing...
python -m pip install -q --disable-pip-version-check -r "%REQ_FILE%"
if errorlevel 1 (
    echo   [X] Failed to install requirements.
    pause
    exit /b 1
)
echo   [OK] All requirements installed

:reqs_done

call :step 5 "Starting program"
if not exist "%MAIN_SCRIPT%" (
    echo   [X] Could not find %MAIN_SCRIPT% in %CD%
    pause
    exit /b 1
)

echo   [OK] Launching %MAIN_SCRIPT%
echo ----------------------------------------
echo.
python "%MAIN_SCRIPT%" %*
set "EXIT_CODE=%errorlevel%"
echo.
echo ----------------------------------------

if not "%EXIT_CODE%"=="0" (
    echo   [!] Program exited with code %EXIT_CODE%.
    pause
)

endlocal & exit /b %EXIT_CODE%

:step
call set "BAR=%%BAR%~1%%"
echo.
echo %BAR%  Step %~1/5: %~2
exit /b 0
