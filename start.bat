@echo off
echo ============================================
echo  Meeting Summarizer - Starting Backend
echo ============================================
echo.

:: Check venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

:: Check Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama does not appear to be running.
    echo Start it with: ollama serve
    echo The server will still start but summarization will fail.
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting FastAPI server on http://localhost:8000
echo.
echo  Docs available at: http://localhost:8000/docs
echo  Press Ctrl+C to stop.
echo.

cd backend
uvicorn main:app --reload --port 8000
