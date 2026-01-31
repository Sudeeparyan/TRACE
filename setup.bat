@echo off
REM ============================================================
REM TRACE - Initial Setup Script for Beginners
REM Run this ONCE before starting the system
REM ============================================================

echo.
echo  ████████╗██████╗  █████╗  ██████╗███████╗
echo  ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
echo     ██║   ██████╔╝███████║██║     █████╗  
echo     ██║   ██╔══██╗██╔══██║██║     ██╔══╝  
echo     ██║   ██║  ██║██║  ██║╚██████╗███████╗
echo     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
echo.
echo  Initial Setup Script
echo  ============================================================
echo.

cd /d "%~dp0"

echo ============================================================
echo  STEP 1: Checking Prerequisites
echo ============================================================
echo.

REM Check for Python
echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed!
    echo.
    echo Please download and install Python 3.10+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check the box that says:
    echo   "Add Python to PATH"
    echo.
    echo After installing, close this window and run setup.bat again.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo   [OK] Python %%i found

REM Check for Node.js
echo [2/3] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Node.js is not installed!
    echo.
    echo Please download and install Node.js 18+ from:
    echo   https://nodejs.org/
    echo.
    echo Choose the LTS version (recommended).
    echo.
    echo After installing, close this window and run setup.bat again.
    echo.
    pause
    exit /b 1
)
for /f %%i in ('node --version') do echo   [OK] Node.js %%i found

REM Check for npm
echo [3/3] Checking npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] npm not found
    pause
    exit /b 1
)
for /f %%i in ('npm --version') do echo   [OK] npm %%i found

echo.
echo ============================================================
echo  STEP 2: Installing Python Dependencies
echo ============================================================
echo.

pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install Python dependencies
    echo Please check the error messages above.
    pause
    exit /b 1
)
echo   [OK] Python dependencies installed

pip install -r client/server/requirements.txt >nul 2>&1
echo   [OK] Server dependencies installed

echo.
echo ============================================================
echo  STEP 3: Installing Node.js Dependencies
echo ============================================================
echo.

cd client
call npm install
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install Node.js dependencies
    echo Please check the error messages above.
    pause
    exit /b 1
)
cd ..
echo   [OK] Node.js dependencies installed

echo.
echo ============================================================
echo  STEP 4: Setting Up Environment Configuration
echo ============================================================
echo.

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo   [OK] Created .env file from template
    echo.
    echo ============================================================
    echo  IMPORTANT: Configure Your API Key
    echo ============================================================
    echo.
    echo To use AI features, you need a Google API Key.
    echo.
    echo 1. Go to: https://aistudio.google.com/app/apikey
    echo 2. Click "Create API Key"
    echo 3. Copy the key
    echo.
    echo The .env file will now open in Notepad.
    echo Find the line: GOOGLE_API_KEY=your_google_api_key_here
    echo Replace "your_google_api_key_here" with your actual API key.
    echo Save the file and close Notepad.
    echo.
    pause
    notepad ".env"
) else (
    echo   [OK] .env file already exists
)

echo.
echo ============================================================
echo  STEP 5: Verifying Installation
echo ============================================================
echo.

echo Testing Principal Agent import...
python -c "from principal_agent.agent import principal_agent; print('  [OK] Principal Agent')" 2>nul
if errorlevel 1 (
    echo   [WARN] Principal Agent import failed - may work after starting
)

echo Testing Google ADK import...
python -c "from google.adk.agents import Agent; print('  [OK] Google ADK')" 2>nul
if errorlevel 1 (
    echo   [WARN] Google ADK import failed - run: pip install google-adk
)

echo Testing Gemini import...
python -c "import google.generativeai; print('  [OK] Google Generative AI')" 2>nul
if errorlevel 1 (
    echo   [WARN] Gemini import failed - run: pip install google-generativeai
)

echo.
echo ============================================================
echo  SETUP COMPLETE!
echo ============================================================
echo.
echo Your TRACE system is now set up. Here's how to run it:
echo.
echo   Option 1: Full System (Dashboard + ADK Chat)
echo            Run: start_full_system.bat
echo.
echo   Option 2: Dashboard Only
echo            Run: start_all.bat
echo.
echo After starting, open your browser to:
echo   Dashboard:  http://localhost:5173
echo   ADK Chat:   http://localhost:8001
echo.
echo For more information, see README.md
echo.
echo ============================================================
echo.
pause
