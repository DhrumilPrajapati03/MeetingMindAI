@echo off
echo ========================================
echo Starting MeetingMind AI UI
echo ========================================
echo.

cd /d "%~dp0\.."

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Starting Streamlit...
echo.
echo Access the app at: http://localhost:8501
echo.

streamlit run ui/app.py

pause