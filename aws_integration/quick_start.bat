@echo off
REM TRACE AWS Integration - Quick Start Script for Windows
REM This script automates the complete deployment process

echo ================================================================================
echo TRACE AWS Integration - Quick Start
echo ================================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/6] Checking Python installation...
python --version
echo.

REM Check AWS CLI installation
aws --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS CLI is not installed
    echo Please install from https://aws.amazon.com/cli/
    pause
    exit /b 1
)

echo [2/6] Checking AWS CLI installation...
aws --version
echo.

REM Check AWS credentials
echo [3/6] Verifying AWS credentials...
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS credentials not configured
    echo Please configure AWS credentials using 'aws configure'
    echo Or ensure .env file has valid credentials
    pause
    exit /b 1
)

echo AWS Account verified
aws sts get-caller-identity
echo.

REM Create virtual environment
echo [4/6] Creating Python virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo Virtual environment created
)
echo.

REM Activate virtual environment
echo [5/6] Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python packages...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo Setup Complete! Ready to deploy.
echo ================================================================================
echo.
echo Next steps:
echo   1. Deploy MCP servers:    python deployment\deploy_mcp_servers.py
echo   2. Test connections:      python tests\test_mcp_connection.py
echo   3. Run principal agent:   python principal_agent_aws.py
echo.
echo To deploy now, press ENTER. To exit, press Ctrl+C
pause

REM Deploy MCP servers
echo.
echo [6/6] Deploying MCP servers to AWS Bedrock AgentCore...
python deployment\deploy_mcp_servers.py --server all

if errorlevel 1 (
    echo.
    echo ERROR: Deployment failed. Check the logs above.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo Deployment Complete!
echo ================================================================================
echo.
echo Testing MCP connections...
python tests\test_mcp_connection.py

echo.
echo ================================================================================
echo TRACE AWS Integration is ready!
echo ================================================================================
echo.
echo To start using the Principal Agent:
echo   python principal_agent_aws.py
echo.
echo For help and documentation:
echo   - AWS_SETUP_GUIDE.md - Complete setup guide
echo   - README_AWS.md - Quick reference
echo.
pause
