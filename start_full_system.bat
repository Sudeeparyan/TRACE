@echo off
REM ============================================================
REM TRACE - Start Full System
REM Runs ADK Web + Dashboard Backend + Frontend
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
echo  ADK Web + Dashboard Integration Mode
echo  ============================================================
echo.

cd /d "%~dp0"

echo ============================================================
echo  STEP 1: Checking Prerequisites
echo ============================================================
echo.

REM Check for Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo   [OK] Python %PYTHON_VER% found

REM Check for Node.js
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo.
    echo Please install Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f %%i in ('node --version') do set NODE_VER=%%i
echo   [OK] Node.js %NODE_VER% found

REM Check for npm
echo Checking npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is not installed
    echo.
    echo npm should come with Node.js installation.
    echo.
    pause
    exit /b 1
)
for /f %%i in ('npm --version') do set NPM_VER=%%i
echo   [OK] npm %NPM_VER% found

REM Check for ADK
echo Checking Google ADK...
python -c "from google.adk.agents import Agent" >nul 2>&1
if errorlevel 1 (
    echo   [WARN] Google ADK not found, installing...
    pip install google-adk >nul 2>&1
    if errorlevel 1 (
        echo   [ERROR] Failed to install google-adk
        echo   Please run: pip install google-adk
        pause
        exit /b 1
    )
)
echo   [OK] Google ADK found

REM Check for .env file
echo Checking environment configuration...
if not exist ".env" (
    echo   [WARN] .env file not found, creating from example...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo   [OK] Created .env from .env.example
        echo.
        echo   IMPORTANT: Please edit .env and add your GOOGLE_API_KEY
        echo   Get your key from: https://aistudio.google.com/app/apikey
        echo.
        notepad ".env"
        echo.
        echo Press any key after you've saved your API key...
        pause >nul
    ) else (
        echo   [ERROR] .env.example not found
        echo   Please create a .env file with your GOOGLE_API_KEY
        pause
        exit /b 1
    )
) else (
    echo   [OK] .env file found
)

REM Check if GOOGLE_API_KEY is set
findstr /C:"GOOGLE_API_KEY=your" ".env" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo   [WARN] GOOGLE_API_KEY is not configured in .env
    echo   Please add your Google API key to the .env file
    echo.
)

REM Check if node_modules exists
if not exist "client\node_modules" (
    echo.
    echo   [INFO] Node modules not found, installing...
    cd client
    call npm install
    cd ..
    if errorlevel 1 (
        echo   [ERROR] Failed to install npm dependencies
        pause
        exit /b 1
    )
    echo   [OK] npm dependencies installed
) else (
    echo   [OK] npm dependencies found
)

echo.
echo ============================================================
echo  STEP 2: Starting Services
echo ============================================================
echo.
echo This script starts:
echo   1. Dashboard Backend (Port 8000) - REST API server
echo   2. ADK Web (Port 8001) - Principal Agent chat interface
echo   3. Frontend (Port 5173) - React dashboard
echo.

REM Start Dashboard Backend on port 8000
echo [1/3] Starting Dashboard Backend (Port 8000)...
start "TRACE Backend" cmd /k "cd /d %~dp0client\server && python dashboard_server.py"

timeout /t 3 /nobreak >nul

REM Start ADK Web on port 8001
echo [2/3] Starting ADK Web Interface (Port 8001)...
start "TRACE ADK Web" cmd /k "cd /d %~dp0 && adk web --port 8001"

timeout /t 3 /nobreak >nul

REM Start Frontend
echo [3/3] Starting Frontend (Port 5173)...
start "TRACE Frontend" cmd /k "cd /d %~dp0client && npm run dev"

echo.
echo ============================================================
echo  TRACE Full System Started!
echo ============================================================
echo.
echo  Services:
echo  ---------------------------------------------------------
echo  Dashboard Backend:  http://localhost:8000/api
echo  ADK Web Interface:  http://localhost:8001
echo  React Dashboard:    http://localhost:5173
echo  ---------------------------------------------------------
echo.
echo  Usage:
echo  - Use the React Dashboard for monitoring and visualization
echo  - Use ADK Web to chat directly with the Principal Agent
echo  - The Dashboard uses ADK for AI-powered auto-remediation
echo.
echo  To stop: Close all three terminal windows
echo.

timeout /t 5 /nobreak >nul

echo Opening interfaces in your browser...
start http://localhost:5173
timeout /t 2 /nobreak >nul
start http://localhost:8001

echo.
echo Press any key to exit this window (services will keep running)...
pause >nul

goto :eof
