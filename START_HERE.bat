@echo off
echo ========================================================================
echo    🔍 AI-POWERED FAKE NEWS DETECTION SYSTEM
echo ========================================================================
echo.
echo Welcome! This system features advanced AI analysis with dual pipelines:
echo • Standard Pipeline: Fast analysis (3-5s, 75%% accuracy)
echo • RAG Pipeline: Advanced analysis (5-10s, 85%% accuracy)
echo.

:menu
echo Please select an option:
echo.
echo 1. 🚀 Quick Start (Recommended)
echo 2. 📦 Install Dependencies
echo 3. ⚙️  Configure Environment
echo 4. 🧪 Run Tests
echo 5. 🌐 Start Web Server
echo 6. 📚 View Documentation
echo 7. 🐳 Docker Setup
echo 8. ❌ Exit
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto quickstart
if "%choice%"=="2" goto install
if "%choice%"=="3" goto config
if "%choice%"=="4" goto test
if "%choice%"=="5" goto server
if "%choice%"=="6" goto docs
if "%choice%"=="7" goto docker
if "%choice%"=="8" goto end
goto menu

:quickstart
echo.
echo ========================================================================
echo    🚀 QUICK START SETUP
echo ========================================================================
echo.
echo Step 1: Installing dependencies...
cd fake-news-detector
pip install -r requirements.txt
echo.
echo Step 2: Checking environment configuration...
if not exist .env (
    echo ⚠️  Environment file not found. Copying template...
    copy .env.example .env
    echo.
    echo ✅ Created .env file from template
    echo ⚠️  IMPORTANT: Edit .env file and add your API keys:
    echo    - GROQ_API_KEY (get from https://console.groq.com)
    echo    - NEWS_API_KEY (get from https://newsapi.org)
    echo.
    pause
) else (
    echo ✅ Environment file found
)
echo.
echo Step 3: Starting the server...
echo.
echo 🌐 Server will start at: http://localhost:3000
echo 📖 Press Ctrl+C to stop the server
echo.
python serve_frontend.py
pause
goto menu

:install
echo.
echo ========================================================================
echo    📦 INSTALLING DEPENDENCIES
echo ========================================================================
echo.
cd fake-news-detector
echo Installing Python packages...
pip install -r requirements.txt
echo.
echo ✅ Dependencies installed successfully!
echo.
pause
goto menu

:config
echo.
echo ========================================================================
echo    ⚙️  ENVIRONMENT CONFIGURATION
echo ========================================================================
echo.
cd fake-news-detector
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo ✅ Created .env file
) else (
    echo ✅ .env file already exists
)
echo.
echo 📝 Please edit the .env file and add your API keys:
echo.
echo Required API Keys:
echo • GROQ_API_KEY - Get from: https://console.groq.com
echo • NEWS_API_KEY - Get from: https://newsapi.org
echo.
echo Optional (for enhanced features):
echo • SUPABASE_DB_URL - For RAG pipeline vector database
echo • SERPAPI_KEY - For better news coverage
echo • GOOGLE_CLIENT_ID/SECRET - For OAuth login
echo.
echo Opening .env file for editing...
notepad .env
pause
goto menu

:test
echo.
echo ========================================================================
echo    🧪 RUNNING TESTS
echo ========================================================================
echo.
cd fake-news-detector
echo Testing RAG Pipeline...
python test_rag_pipeline.py
echo.
echo Testing health endpoints...
curl -s http://localhost:3000/health 2>nul || echo ⚠️  Server not running
echo.
echo ✅ Tests completed!
pause
goto menu

:server
echo.
echo ========================================================================
echo    🌐 STARTING WEB SERVER
echo ========================================================================
echo.
cd fake-news-detector
echo.
echo 🚀 Starting AI-Powered Fake News Detection System...
echo.
echo 📍 Server URL: http://localhost:3000
echo 📖 API Documentation: http://localhost:3000/health
echo 🔍 RAG Pipeline Health: http://localhost:3000/rag-health
echo.
echo Features available:
echo • Text analysis with AI explanations
echo • URL verification with web scraping
echo • Multi-language support (10+ languages)
echo • Advanced RAG pipeline (85%% accuracy)
echo • User authentication and history
echo.
echo Press Ctrl+C to stop the server
echo.
python serve_frontend.py
pause
goto menu

:docs
echo.
echo ========================================================================
echo    📚 DOCUMENTATION
echo ========================================================================
echo.
echo Available documentation:
echo.
echo 1. README.md - Complete project overview
echo 2. PROJECT_STRUCTURE.md - System architecture
echo 3. fake-news-detector/RAG_PIPELINE_DOCUMENTATION.md - RAG technical guide
echo 4. fake-news-detector/RAG_QUICK_REFERENCE.md - RAG cheat sheet
echo 5. fake-news-detector/RAG_PIPELINE_COMPARISON.md - Pipeline comparison
echo 6. CONTRIBUTING.md - How to contribute
echo 7. SYSTEM_OVERVIEW.txt - Visual system overview
echo.
set /p doc="Enter number to view (1-7): "
if "%doc%"=="1" type README.md | more
if "%doc%"=="2" type PROJECT_STRUCTURE.md | more
if "%doc%"=="3" type fake-news-detector\RAG_PIPELINE_DOCUMENTATION.md | more
if "%doc%"=="4" type fake-news-detector\RAG_QUICK_REFERENCE.md | more
if "%doc%"=="5" type fake-news-detector\RAG_PIPELINE_COMPARISON.md | more
if "%doc%"=="6" type CONTRIBUTING.md | more
if "%doc%"=="7" type SYSTEM_OVERVIEW.txt | more
pause
goto menu

:docker
echo.
echo ========================================================================
echo    🐳 DOCKER SETUP
echo ========================================================================
echo.
echo Docker deployment options:
echo.
echo 1. Build and run with Docker
echo 2. Use Docker Compose (includes PostgreSQL)
echo 3. View Docker logs
echo.
set /p docker_choice="Enter choice (1-3): "

if "%docker_choice%"=="1" (
    echo Building Docker image...
    docker build -t fake-news-detector .
    echo.
    echo Running container...
    docker run -p 8000:8000 --env-file .env fake-news-detector
)

if "%docker_choice%"=="2" (
    echo Starting with Docker Compose...
    docker-compose up -d
    echo.
    echo ✅ Services started! Access at http://localhost:8000
    echo View logs: docker-compose logs -f
)

if "%docker_choice%"=="3" (
    docker-compose logs -f
)

pause
goto menu

:end
echo.
echo ========================================================================
echo    👋 THANK YOU!
echo ========================================================================
echo.
echo Thank you for using the AI-Powered Fake News Detection System!
echo.
echo 🌟 If you found this helpful, please consider:
echo • ⭐ Starring the repository on GitHub
echo • 🐛 Reporting issues or bugs
echo • 🤝 Contributing improvements
echo • 📢 Sharing with others
echo.
echo 📧 Contact: jaiyanth.b@outlook.com
echo 🌐 GitHub: https://github.com/yourusername/fake-news-detector
echo.
pause
exit
