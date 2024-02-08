@echo off
setlocal

@REM CONFIG
set TOP_DIR=%~dp0\..
set PYTHON_VERSION=3.11

echo Check Python version...

cd "%TOP_DIR%"
set PY="%TOP_DIR%\.venv\Scripts\python"

echo Create python virtual enviornment...

py -%PYTHON_VERSION% --version || exit /b
py -%PYTHON_VERSION% -m venv .venv || exit /b

echo Install requirements...

%PY% -m pip install --upgrade pip
%PY% -m pip install -r "%TOP_DIR%/requirements.txt"
