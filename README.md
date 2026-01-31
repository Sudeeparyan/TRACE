# TRACE - Traffic & Resource Agentic Control Engine

**TRACE** is an intelligent telecom network management system powered by AI agents. It provides real-time monitoring, anomaly detection, and automated self-healing capabilities for network infrastructure.

---

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Local)](#quick-start-local)
4. [Detailed Setup Guide](#detailed-setup-guide)
5. [Running the System](#running-the-system)
6. [AWS Deployment](#aws-deployment)
7. [Project Structure](#project-structure)
8. [Troubleshooting](#troubleshooting)
9. [Configuration](#configuration)

---

## Features

- **Real-time Dashboard**: Monitor network health, energy consumption, and congestion
- **AI-Powered Analysis**: Uses Google Gemini or AWS Bedrock for intelligent insights
- **Auto-Remediation**: Automated issue detection and resolution
- **Principal Agent (ADK)**: Conversational AI interface for network management
- **Multi-Provider Support**: Works with Google Gemini, AWS Bedrock, or standalone

---

## Prerequisites

Before starting, ensure you have the following installed:

### Required Software

| Software | Version | Download Link |
|----------|---------|---------------|
| **Python** | 3.10 or higher | https://www.python.org/downloads/ |
| **Node.js** | 18 or higher | https://nodejs.org/ |
| **Git** | Latest | https://git-scm.com/ |

### Verify Installation

Open a terminal (Command Prompt or PowerShell) and run:

```bash
# Check Python version
python --version
# Expected: Python 3.10.x or higher

# Check Node.js version
node --version
# Expected: v18.x.x or higher

# Check npm version
npm --version
# Expected: 9.x.x or higher
```

### API Keys (Choose One)

- **Google API Key** (for Gemini AI): Get from https://aistudio.google.com/app/apikey
- **AWS Credentials** (for Bedrock): Get from AWS Console

---

## Quick Start (Local)

### Step 1: Navigate to Project

```bash
cd D:\AI\trace\TRACE
```

### Step 2: Run Setup Script (First Time Only)

```bash
setup.bat
```

This will:
- Check prerequisites (Python, Node.js)
- Install all dependencies
- Create .env file from template
- Open .env for you to add your API key

### Step 3: Start the System

```bash
# Option 1: Start full system (recommended)
start_full_system.bat

# Option 2: Start just dashboard
start_all.bat
```

### Step 4: Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:5173 | React Dashboard UI |
| **Backend API** | http://localhost:8000 | Dashboard REST API |
| **ADK Web** | http://localhost:8001 | Principal Agent Chat |

---

## Detailed Setup Guide

### 1. Python Environment Setup

```bash
# Navigate to project root
cd D:\AI\trace\TRACE

# Create a virtual environment (recommended)
python -m venv .venv

# Activate the virtual environment
# Windows Command Prompt:
.venv\Scripts\activate.bat

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install all Python dependencies
pip install -r requirements.txt

# Install client server dependencies
pip install -r client/server/requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
copy .env.example .env
```

Edit the `.env` file with your settings:

```env
# GOOGLE API (Required for Local/Gemini Mode)
# Get your API key from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here

# AWS CREDENTIALS (Required for AWS Mode)
# Get from AWS Console > IAM > Security Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# MODEL CONFIGURATION
DEFAULT_MODEL=gemini-2.0-flash
TEMPERATURE=0.7

# AI BACKEND: auto, gemini, or bedrock
TRACE_AI_BACKEND=auto
```

### 3. Node.js Frontend Setup

```bash
# Navigate to client folder
cd client

# Install dependencies
npm install

# Return to root
cd ..
```

### 4. Verify Installation

```bash
# Test Python imports
python -c "from principal_agent.agent import principal_agent; print('Principal Agent: OK')"

# Test ADK installation
python -c "from google.adk.agents import Agent; print('ADK: OK')"

# Test Gemini
python -c "import google.generativeai; print('Gemini: OK')"
```

---

## Running the System

### Option 1: Full System (Recommended)

Starts Dashboard Backend, ADK Web, and React Frontend:

```bash
start_full_system.bat
```

This opens:
- **Dashboard Frontend**: http://localhost:5173
- **Dashboard API**: http://localhost:8000/api
- **ADK Web Interface**: http://localhost:8001

### Option 2: Dashboard Only

Starts only the backend and frontend (no ADK chat):

```bash
start_all.bat
```

Or specify a mode:

```bash
start_all.bat all       # Backend + Frontend (default)
start_all.bat backend   # Backend only
start_all.bat frontend  # Frontend only
start_all.bat adk       # ADK Web only
```

### Option 3: Manual Start (Each Component)

**Terminal 1 - Backend Server:**
```bash
cd client\server
python dashboard_server.py
```

**Terminal 2 - Frontend:**
```bash
cd client
npm run dev
```

**Terminal 3 - ADK Web (Optional):**
```bash
adk web --port 8001
```

### Verify System is Running

1. Open http://localhost:5173 in your browser
2. You should see the TRACE Dashboard
3. Check the terminal windows for any errors

Expected console output:
```
============================================================
TRACE Dashboard Server - Integration Status
============================================================
  Principal Agent: [OK] Available
  ADK Framework:   [OK] Available
  Gemini AI:       [OK] Available
  AWS Bedrock:     [--] Not Available (unless configured)
  Mode:            INTEGRATED
============================================================
```

---

## AWS Deployment

### Prerequisites for AWS

1. **AWS Account** with admin access
2. **AWS CLI** installed and configured
3. **AWS Credentials** in your `.env` file

### Step 1: Configure AWS Credentials

Edit your `.env` file:

```env
AWS_ACCESS_KEY_ID=AKIA...your_key...
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### Step 2: Verify AWS Access

```bash
# Install boto3 if not already installed
pip install boto3

# Test AWS connection
python -c "import boto3; client = boto3.client('sts'); print(client.get_caller_identity())"
```

### Step 3: Deploy MCP Servers to Bedrock

```bash
cd extrafiles\AWS_Integration
python deployment\deploy_mcp_servers.py --server all
```

### Step 4: Run with AWS Backend

Set the AI backend to Bedrock in your .env:

```env
TRACE_AI_BACKEND=bedrock
```

Then start the system:

```bash
start_full_system.bat
```

### AWS Services Used

| Service | Purpose |
|---------|---------|
| **Bedrock AgentCore** | AI agent runtime with Claude models |
| **IAM** | Role-based access control |
| **Cognito** | JWT authentication |
| **SSM Parameter Store** | Configuration management |
| **Secrets Manager** | Secure credential storage |
| **CloudWatch** | Logging and monitoring |

For detailed AWS setup, see: `extrafiles/AWS_Integration/AWS_SETUP_GUIDE.md`

---

## Project Structure

```
TRACE/
|-- .env                      # Environment variables (create from .env.example)
|-- .env.example              # Example environment template
|-- requirements.txt          # Python dependencies
|-- setup.bat                 # First-time setup script
|-- start_all.bat             # Start dashboard (backend + frontend)
|-- start_full_system.bat     # Start full system (+ ADK web)
|-- README.md                 # This file
|
|-- principal_agent/          # AI Agent (Google ADK)
|   |-- agent.py              # Main Principal Agent definition
|   |-- config/               # Agent configuration
|   |-- parent_agents/        # Regional coordinator agents
|   |-- tools/                # Agent tools (health, remediation, etc.)
|
|-- client/                   # React Dashboard
|   |-- package.json          # Node.js dependencies
|   |-- vite.config.js        # Vite build configuration
|   |-- src/                  # React source code
|   |   |-- App.jsx           # Main React app
|   |   |-- components/       # UI components
|   |   |-- services/         # API services
|   |-- server/               # Python backend
|       |-- dashboard_server.py       # Flask server
|       |-- agent_integration.py      # Agent bridge
|       |-- gemini_service.py         # Gemini AI service
|       |-- requirements.txt          # Server dependencies
|
|-- data/                     # Sample telemetry data
|   |-- trace_reduced_20.json # 20 sample records
|
|-- AWS/                      # AWS deployment files
|   |-- cloudformation/       # CloudFormation templates
|   |-- lambda/               # Lambda functions
|   |-- mcp_servers/          # MCP server implementations
|
|-- extrafiles/               # Additional documentation
    |-- AWS_Integration/      # AWS setup guides
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "Python is not recognized"

**Solution**: Add Python to your PATH:
- Reinstall Python and check "Add Python to PATH"
- Or manually add: `C:\Users\YourName\AppData\Local\Programs\Python\Python310\`

#### 2. "npm is not recognized"

**Solution**: Install Node.js from https://nodejs.org/ and restart your terminal.

#### 3. "Module not found: google.adk"

**Solution**: Install the Google ADK package:
```bash
pip install google-adk
```

#### 4. "GOOGLE_API_KEY not found" or "401 Unauthorized"

**Solution**: 
1. Get an API key from https://aistudio.google.com/app/apikey
2. Add it to your `.env` file:
   ```env
   GOOGLE_API_KEY=your_key_here
   ```

#### 5. "Port 8000 already in use"

**Solution**: Kill the existing process:
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with the actual number)
taskkill /PID <PID> /F
```

#### 6. "Cannot connect to backend" (Frontend error)

**Solution**: Ensure the backend is running on port 8000:
```bash
cd client\server
python dashboard_server.py
```

#### 7. "npm install fails"

**Solution**: Clear npm cache and retry:
```bash
npm cache clean --force
rd /s /q node_modules
npm install
```

#### 8. "ADK web command not found"

**Solution**: Install ADK and ensure it's in PATH:
```bash
pip install google-adk
# Then restart your terminal
```

#### 9. "eventlet/ssl issues on Windows"

**Solution**: The server auto-handles this, but if issues persist:
```bash
pip install eventlet==0.33.3
pip install dnspython==2.3.0
```

#### 10. "Principal Agent not available"

**Solution**: Ensure you're running from the correct directory:
```bash
cd D:\AI\trace\TRACE
python -c "from principal_agent.agent import principal_agent; print('OK')"
```

### Still Having Issues?

1. Check all three terminal windows for error messages
2. Ensure `.env` file exists and has correct values
3. Try running each component manually to isolate the issue
4. Check firewall settings for ports 5173, 8000, 8001

---

## Configuration

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | - | Google AI API key (required for Gemini) |
| `AWS_ACCESS_KEY_ID` | - | AWS access key (required for Bedrock) |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key (required for Bedrock) |
| `AWS_REGION` | us-east-1 | AWS region |
| `TRACE_AI_BACKEND` | auto | AI backend: auto, gemini, bedrock |
| `DEFAULT_MODEL` | gemini-2.0-flash | Default AI model |
| `LOG_LEVEL` | INFO | Logging level |

### Ports Reference

| Service | Port | Config File |
|---------|------|-------------|
| React Frontend | 5173 | vite.config.js |
| Backend API | 8000 | dashboard_server.py |
| ADK Web | 8001 | start_full_system.bat |

---

## Support

- **Documentation**: See `extrafiles/` folder for detailed guides
- **AWS Setup**: See `extrafiles/AWS_Integration/START_HERE.md`
- **Architecture**: See `extrafiles/archived_docs/architecture.md`

---

## License

MIT License - See LICENSE file for details.

---

**Happy Monitoring!**
