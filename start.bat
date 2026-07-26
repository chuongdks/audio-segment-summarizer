@echo off
echo ============================================
echo  Meeting Summarizer - Starting
echo ============================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama does not appear to be running.
    echo Start it with: ollama serve
    echo.
)

echo [1/2] Starting Python backend...
echo  Docs available at: http://localhost:8000/docs
call venv\Scripts\activate.bat
start "Meeting Summarizer - Backend" cmd /k "cd backend && uvicorn main:app --port 8000"

echo [2/2] Starting Electron frontend...
timeout /t 2 /nobreak >nul
cd frontend
start "Meeting Summarizer - Frontend" cmd /k "npm run start"

echo.
echo Both processes are running in separate windows.
echo Close those windows to stop the app.
