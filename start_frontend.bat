@echo off
title TRAFFICGUARD FRONTEND (Next.js 14 Web App)
color 0A
cd /d "%~dp0web-app"
echo ========================================================
echo   [TRAFFICGUARD] FRONTEND NEXT.JS WEB APP
echo   - Local URL: http://localhost:3000
echo   - Live Monitor: http://localhost:3000/live
echo   - Simulator: http://localhost:3000/simulator
echo   - AI Status: http://localhost:3000/ai-status
echo ========================================================
echo.
if not exist "node_modules" (
    echo Thu muc node_modules chua ton tai. Dang tu dong cai dat thu vien npm...
    call npm install
)

npm run dev
echo.
echo Frontend da dung lai.
pause
