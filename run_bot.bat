@echo off
echo ========================================
echo 🤖 ElixirMind Bot Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo ⚠️  Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

REM Check if dependencies are installed
python -c "import cv2, numpy, pyautogui, mss" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Installing missing dependencies...
    pip install opencv-python numpy pyautogui mss
)

REM Run auto-configuration if not done
if not exist auto_config.json (
    echo 🔧 Running auto-configuration...
    python auto_configurator.py
)

REM Start the bot
echo.
echo 🚀 Starting ElixirMind Bot...
echo 📊 Dashboard will be available at: http://localhost:8501
echo.
python main.py --mode real --strategy heuristic

pause
