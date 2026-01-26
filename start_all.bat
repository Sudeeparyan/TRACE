@echo off
REM ============================================================
REM TRACE - Unified Start Script
REM Runs Dashboard Backend + Frontend + Optional ADK Web
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo  ████████╗██████╗  █████╗  ██████╗███████╗
echo  ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
echo     ██║   ██████╔╝███████║██║     █████╗  
echo     ██║   ██╔══██╗██╔══██║██║     ██╔══╝  
echo     ██║   ██║  ██║██║  ██║╚██████╗███████╗
echo     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
echo.
echo  Traffic ^& Resource Agentic Control Engine
echo  ============================================================
echo.

cd /d "%~dp0"

REM Check for help flag
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help

REM Default mode: all
set MODE=all
if not "%1"=="" set MODE=%1

if "%MODE%"=="backend" goto :start_backend
if "%MODE%"=="frontend" goto :start_frontend
if "%MODE%"=="adk" goto :start_adk
if "%MODE%"=="all" goto :start_all

echo Invalid mode: %MODE%
goto :show_help

:show_help
echo Usage: start_trace.bat [mode]
echo.
echo Modes:
echo   all       - Start backend + frontend (default)
echo   backend   - Start only the dashboard backend server
echo   frontend  - Start only the Vite frontend
echo   adk       - Start only the ADK web interface
echo.
echo Examples:
echo   start_trace.bat           # Start dashboard (backend + frontend)
echo   start_trace.bat all       # Same as above
echo   start_trace.bat backend   # Start backend only
echo   start_trace.bat adk       # Start ADK web only
echo.
echo Ports:
echo   Dashboard Backend: http://localhost:8000
echo   Frontend:         http://localhost:5173
echo   ADK Web:          http://localhost:8000 (when running adk mode)
echo.
goto :eof

:start_backend
echo [1/1] Starting Dashboard Backend Server...
echo.
cd client\server
python dashboard_server.py
goto :eof

:start_frontend
echo [1/1] Starting Frontend Development Server...
echo.
cd client
npm run dev
goto :eof

:start_adk
echo [1/1] Starting ADK Web Interface...
echo.
echo The Principal Agent will be available at http://localhost:8000
echo.
adk web
goto :eof

:start_all
echo Starting TRACE Dashboard (Backend + Frontend)...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/2] Starting Dashboard Backend Server (Port 8000)...
start "TRACE Backend" cmd /k "cd /d %~dp0client\server && python dashboard_server.py"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Development Server (Port 5173)...
start "TRACE Frontend" cmd /k "cd /d %~dp0client && npm run dev"

echo.
echo ============================================================
echo TRACE Dashboard is starting!
echo ============================================================
echo.
echo  Dashboard Backend: http://localhost:8000
echo  Frontend:         http://localhost:5173
echo.
echo  To start ADK Web separately, run: start_trace.bat adk
echo.
echo  Press any key to open the dashboard in your browser...
pause >nul

start http://localhost:5173

goto :eof
