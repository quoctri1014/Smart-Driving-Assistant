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
npm run dev
echo.
echo Frontend da dung lai.
pause
