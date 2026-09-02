@echo off
title AI News Verification System
echo ========================================================================
echo    🔍 AI NEWS VERIFICATION SYSTEM (FastAPI + Groq + Vector RAG)
echo ========================================================================
echo.
echo Welcome! This system verifies news claims against real-time news reporting
echo using Groq LLM, Semantic Vector Search, and multi-source evidence retrieval.
echo.

:menu
echo Please select an option:
echo.
echo 1. 🚀 Start Web Application (Recommended)
echo 2. 📦 Install Dependencies
echo 3. 🧪 Run Test Suite (Pytest)
echo 4. ⚙️  Configure Environment (.env)
echo 5. ❌ Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto server
if "%choice%"=="2" goto install
if "%choice%"=="3" goto test
if "%choice%"=="4" goto config
if "%choice%"=="5" goto end
goto menu

:server
echo.
echo ========================================================================
echo    🚀 STARTING FASTAPI SERVER
echo ========================================================================
echo.
if not exist .env (
    echo [INFO] .env file not found. Creating from template...
    copy .env.example .env
    echo [NOTE] Remember to add your GROQ_API_KEY and NEWS_API_KEY to .env!
    echo.
)
echo Starting server at http://localhost:8000 ...
echo Swagger UI docs at http://localhost:8000/docs ...
echo.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
goto menu

:install
echo.
echo Installing Python dependencies...
python -m pip install -r requirements.txt
echo.
echo Done!
pause
goto menu

:test
echo.
echo Running Automated Test Suite...
python -m pytest backend/tests/ -v
echo.
pause
goto menu

:config
if not exist .env (
    copy .env.example .env
    echo Created .env file.
)
notepad .env
goto menu

:end
echo Exiting...
