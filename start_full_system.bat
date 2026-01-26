@echo off
REM ============================================================
REM TRACE - Start ADK Web + Dashboard Backend
REM Runs ADK web interface alongside the dashboard backend
REM ============================================================

echo.
echo  ████████╗██████╗  █████╗  ██████╗███████╗
echo  ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
echo     ██║   ██████╔╝███████║██║     █████╗  
echo     ██║   ██╔══██╗██╔══██║██║     ██╔══╝  
echo     ██║   ██║  ██║██║  ██║╚██████╗███████╗
echo     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
echo.
echo  ADK Web + Dashboard Integration Mode
echo  ============================================================
echo.

cd /d "%~dp0"

echo This script starts:
echo   1. Dashboard Backend (Port 8000) - For dashboard API
echo   2. ADK Web (Port 8001) - For direct agent interaction
echo   3. Frontend (Port 5173) - React dashboard
echo.

REM Start Dashboard Backend on port 8000
echo [1/3] Starting Dashboard Backend (Port 8000)...
start "TRACE Backend" cmd /k "cd /d %~dp0client\server && python dashboard_server.py"

timeout /t 2 /nobreak >nul

REM Start ADK Web on port 8001
echo [2/3] Starting ADK Web Interface (Port 8001)...
start "TRACE ADK Web" cmd /k "cd /d %~dp0 && adk web --port 8001"

timeout /t 2 /nobreak >nul

REM Start Frontend
echo [3/3] Starting Frontend (Port 5173)...
start "TRACE Frontend" cmd /k "cd /d %~dp0client && npm run dev"

echo.
echo ============================================================
echo TRACE Full System Started!
echo ============================================================
echo.
echo  Dashboard Backend:  http://localhost:8000/api
echo  ADK Web Interface:  http://localhost:8001
echo  React Dashboard:    http://localhost:5173
echo.
echo  ADK Web allows direct chat with the Principal Agent.
echo  The Dashboard uses ADK for AI-powered auto-remediation.
echo.
echo Press any key to open both interfaces in your browser...
pause >nul

start http://localhost:5173
timeout /t 1 /nobreak >nul
start http://localhost:8001

goto :eof
