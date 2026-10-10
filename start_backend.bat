@echo off
title TRAFFICGUARD BACKEND (FastAPI + AI Models)
color 0B
cd /d "%~dp0"
echo ========================================================
echo   [TRAFFICGUARD] BACKEND FASTAPI + AI INFERENCE ENGINE
echo   - Host: http://localhost:8000
echo   - Health: http://localhost:8000/health
echo   - Swagger API Docs: http://localhost:8000/docs
echo   - WebSocket Stream: ws://localhost:8000/ws/v1/stream
echo ========================================================
echo.
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo Server da dung lai.
pause
