@echo off
setlocal

@REM CONFIG
set TOP_DIR=%~dp0\..
set PYTHON_VERSION=3.11

cd "%TOP_DIR%"
set PY="%TOP_DIR%\.venv\Scripts\python"

%PY% "%TOP_DIR%\metroid-prime-demofile\main.py"
