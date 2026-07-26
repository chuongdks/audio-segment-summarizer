@echo off
echo ============================================
echo  Meeting Summarizer - First Time Setup
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Download from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause & exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Download from https://nodejs.org/
    pause & exit /b 1
)

echo [1/5] Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/5] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo [3/5] Installing Python dependencies...
pip install -r backend\requirements.txt
if errorlevel 1 ( echo [ERROR] Python deps failed. & pause & exit /b 1 )

echo [4/5] Installing Node dependencies...
cd frontend
npm install
if errorlevel 1 ( echo [ERROR] Node deps failed. & pause & exit /b 1 )
cd ..

echo [5/5] Done.
echo.
echo ============================================
echo  Setup complete!
echo ============================================
echo.
echo Next steps:
echo   1. Install Ollama: https://ollama.com
echo   2. Run: ollama pull llama3.1:8b
echo   3. Double-click start.bat to launch the app
echo.
pause
