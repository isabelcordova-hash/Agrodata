@echo off
setlocal
if exist "%~dp0..\.pgdata\PG_VERSION" (
  "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" -D "%~dp0..\.pgdata" status >nul 2>&1
  if errorlevel 1 (
    "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" -D "%~dp0..\.pgdata" -l NUL -o "-p 55432 -h 127.0.0.1" start
    if errorlevel 1 exit /b 1
  )
)
cd /d "%~dp0..\backend"
if not exist ".venv\Scripts\python.exe" (
  echo Falta backend\.venv. Consulta la instalacion en README.md.
  exit /b 1
)
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
