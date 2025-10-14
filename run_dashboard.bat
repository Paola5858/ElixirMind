@echo off
echo ========================================
echo 📊 ElixirMind Dashboard Launcher
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
if exist venv (
    call venv\Scripts\activate
) else (
    echo ⚠️  Virtual environment not found. Installing dependencies...
    pip install streamlit plotly pandas
)

REM Check if streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Installing Streamlit...
    pip install streamlit plotly pandas
)

REM Start dashboard
echo.
echo 🚀 Starting ElixirMind Dashboard...
echo 📊 Opening browser at: http://localhost:8501
echo.
streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0

pause
