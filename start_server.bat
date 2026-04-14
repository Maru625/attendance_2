@echo off
cd /d "%~dp0"
echo [Attendance] Starting FastAPI server on port 8000...
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
