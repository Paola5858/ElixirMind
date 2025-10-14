@echo off
echo ========================================
echo 🧪 ElixirMind Test Suite
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
    echo ⚠️  Virtual environment not found. Installing test dependencies...
    pip install pytest pytest-cov pytest-benchmark
)

REM Run tests
echo.
echo 🧪 Running test suite...
echo.

REM Basic functionality tests
echo 📋 Running basic tests...
pytest tests/test_detector.py tests/test_actions.py -v --tb=short

if errorlevel 1 (
    echo ❌ Basic tests failed!
    goto :error
)

REM Performance tests
echo.
echo ⚡ Running performance tests...
pytest tests/test_performance.py --benchmark-only -q

REM Coverage report
echo.
echo 📊 Generating coverage report...
pytest --cov=ElixirMind --cov-report=html tests/

echo.
echo ✅ All tests completed successfully!
echo 📊 Coverage report: htmlcov/index.html
goto :end

:error
echo.
echo ❌ Some tests failed. Check the output above for details.
pause
exit /b 1

:end
echo.
echo 🎉 Test suite completed!
pause
