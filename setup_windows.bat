@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  🖥️ JARVIS AI — Windows Setup & Run Script
REM  ═══════════════════════════════════════════════════════════════════════════
REM  Run this on your Windows laptop to set up and start JARVIS.
REM  Requirements: Python 3.11+, Node.js 18+
REM ═══════════════════════════════════════════════════════════════════════════

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║     🖥️  JARVIS AI — Windows Setup Script v10.0          ║
echo ║     Installing your personal AI assistant...             ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ═══ Check Python ═══
echo [1/6] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   ❌ Python not found!
    echo   📥 Download from: https://www.python.org/downloads/
    echo   ⚠️  Check "Add Python to PATH" during install!
    pause
    start https://www.python.org/downloads/
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo   ✅ %%i

REM ═══ Check Node.js ═══
echo [2/6] Checking Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   ❌ Node.js not found!
    echo   📥 Download from: https://nodejs.org/
    pause
    start https://nodejs.org/
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do echo   ✅ Node.js %%i

REM ═══ Create Virtual Environment ═══
echo [3/6] Setting up Python environment...
if not exist ".venv" (
    python -m venv .venv
    echo   ✅ Virtual environment created
) else (
    echo   ✅ Virtual environment exists
)

REM Activate venv
call .venv\Scripts\activate.bat

REM ═══ Install Python Dependencies ═══
echo [4/6] Installing Python dependencies...
pip install -r requirements.txt -q 2>nul
echo   ✅ Python dependencies installed

REM ═══ Setup Desktop App ═══
echo [5/6] Setting up Desktop App...
cd desktop-app
if not exist "node_modules" (
    call npm install 2>nul
)
echo   ✅ Electron app ready

REM ═══ Build Frontend (if needed) ═══
cd ..
if exist "telegram-mini-app\package.json" (
    if not exist "telegram-mini-app\dist" (
        echo   📦 Building frontend...
        cd telegram-mini-app
        if not exist "node_modules" call npm install 2>nul
        call npm run build 2>nul
        cd ..
    )
)
echo   ✅ Frontend ready

REM ═══ Create .env if not exists ═══
if not exist ".env" (
    echo [6/6] Creating default .env configuration...
    (
        echo # JARVIS AI Configuration
        echo # Add your API keys below
        echo PORT=8000
        echo APP_MODE=desktop
        echo.
        echo # AI Providers ^(add at least one^)
        echo # GROQ_API_KEY=your_groq_key_here
        echo # OPENAI_API_KEY=your_openai_key_here
        echo # ANTHROPIC_API_KEY=your_anthropic_key_here
        echo # GOOGLE_API_KEY=your_gemini_key_here
    ) > .env
    echo   ✅ Default .env created — add your API keys!
) else (
    echo [6/6] .env exists ✅
)

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║     ✅ JARVIS AI Setup Complete!                         ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║                                                          ║
echo ║  To start JARVIS:                                        ║
echo ║    1. Double-click "start_jarvis_desktop.bat"            ║
echo ║    2. Or run: cd desktop-app ^&^& npm start              ║
echo ║                                                          ║
echo ║  Global Hotkey: Ctrl+Shift+J to summon JARVIS            ║
echo ║                                                          ║
echo ║  ⚠️  Add your API keys to .env file first!               ║
echo ║     (GROQ_API_KEY, OPENAI_API_KEY, etc.)                 ║
echo ║                                                          ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
pause
