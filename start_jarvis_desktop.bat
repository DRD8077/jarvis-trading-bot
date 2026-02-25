@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  🚀 JARVIS AI — Desktop Launcher for Windows
REM  ═══════════════════════════════════════════════════════════════════════════
REM  Starts both the Python backend + Electron desktop app.
REM  JARVIS will have FULL control of your laptop.
REM ═══════════════════════════════════════════════════════════════════════════

@echo off
title JARVIS AI — Starting Up...
color 0B

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║     🤖 JARVIS AI — Iron Man Edition                      ║
echo ║     Starting your personal AI assistant...               ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ═══ Load environment ═══
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b" 2>nul
        )
    )
)

REM ═══ Activate virtual environment ═══
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo   ✅ Python environment activated
)

REM ═══ Set defaults ═══
if not defined PORT set PORT=8000
set APP_MODE=desktop
set PYTHONPATH=%cd%

REM ═══ Start Python Backend (hidden window) ═══
echo   🧠 Starting AI Backend on port %PORT%...
start /B /MIN "JARVIS-Backend" cmd /c "python -m uvicorn jarvis_standalone_server:app --host 127.0.0.1 --port %PORT% --log-level info 2>&1"

REM ═══ Wait for backend to be ready ═══
echo   ⏳ Waiting for backend...
set READY=0
for /L %%i in (1,1,20) do (
    if !READY!==0 (
        timeout /t 1 /nobreak >nul
        curl -s -o nul http://127.0.0.1:%PORT%/health 2>nul
        if !ERRORLEVEL!==0 (
            set READY=1
            echo   ✅ Backend ready!
        )
    )
)

REM ═══ Start Electron Desktop App ═══
echo   🖥️ Starting JARVIS Desktop...
cd desktop-app
start "" npm start -- --no-sandbox
cd ..

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║     ✅ JARVIS AI is LIVE!                                ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║                                                          ║
echo ║  🖥️ Desktop:  JARVIS AI window                          ║
echo ║  🌐 API:      http://127.0.0.1:%PORT%                       ║
echo ║  🔑 Hotkey:   Ctrl+Shift+J (toggle JARVIS)              ║
echo ║  🎤 Voice:    Ctrl+Shift+V (voice mode)                 ║
echo ║                                                          ║
echo ║  💡 JARVIS can:                                          ║
echo ║    "Open Chrome"                                         ║
echo ║    "Set volume to 50"                                    ║
echo ║    "Take a screenshot"                                   ║
echo ║    "Shutdown PC in 10 minutes"                           ║
echo ║    "Search for documents about taxes"                    ║
echo ║    "What's my system status?"                            ║
echo ║    "Play Arijit Singh on YouTube"                        ║
echo ║    "Send WhatsApp to +91..."                             ║
echo ║    "Write Python code to sort a list"                    ║
echo ║                                                          ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo   Press Ctrl+C to stop JARVIS
echo.
pause
