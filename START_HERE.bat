@echo off
echo ========================================================================
echo    FAKE NEWS DETECTION SYSTEM - Quick Start
echo ========================================================================
echo.

:menu
echo Please select an option:
echo.
echo 1. Install Dependencies
echo 2. Download NLTK Data
echo 3. Run Tests
echo 4. Start Enhanced API Server
echo 5. Start Original App
echo 6. View System Architecture
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto nltk
if "%choice%"=="3" goto test
if "%choice%"=="4" goto enhanced
if "%choice%"=="5" goto original
if "%choice%"=="6" goto docs
if "%choice%"=="7" goto end
goto menu

:install
echo.
echo Installing dependencies...
cd fake_news_detector
pip install -r requirements.txt
echo.
echo Dependencies installed!
pause
goto menu

:nltk
echo.
echo Downloading NLTK data...
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
echo.
echo NLTK data downloaded!
pause
goto menu

:test
echo.
echo Running comprehensive tests...
cd fake_news_detector\training\backend
python test_pipeline.py
pause
goto menu

:enhanced
echo.
echo Starting Enhanced API Server...
echo.
echo The server will start at http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
cd fake_news_detector\training\backend
python api_enhanced.py
pause
goto menu

:original
echo.
echo Starting Original Application...
echo.
echo The server will start at http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
cd fake_news_detector\training\backend
python app.py
pause
goto menu

:docs
echo.
echo ========================================================================
echo    DOCUMENTATION FILES
echo ========================================================================
echo.
echo 1. SYSTEM_OVERVIEW.txt - Quick visual overview
echo 2. fake_news_detector\SYSTEM_ARCHITECTURE.md - Complete documentation
echo 3. fake_news_detector\QUICK_START.md - Getting started guide
echo 4. IMPLEMENTATION_SUMMARY.md - Implementation details
echo 5. README.md - Project overview
echo.
echo Opening SYSTEM_OVERVIEW.txt...
type SYSTEM_OVERVIEW.txt | more
pause
goto menu

:end
echo.
echo Thank you for using Fake News Detection System!
echo.
pause
exit
