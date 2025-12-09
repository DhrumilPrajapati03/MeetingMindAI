@echo off
echo Starting Celery Worker...
cd /d "%~dp0\.."
call venv\Scripts\activate
python scripts\start_celery.py
pause