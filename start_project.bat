@echo off
title TRAFFICGUARD SYSTEM LAUNCHER
cd /d "%~dp0"
echo ========================================================
echo   KHOI DONG HE THONG TRAFFICGUARD TREN 2 CUA SO TERMINAL
echo ========================================================
echo [1/2] Dang mo cua so Backend FastAPI (Port 8000)...
start "TRAFFICGUARD BACKEND" cmd /k ""%~dp0start_backend.bat""
timeout /t 3 /nobreak >nul
echo [2/2] Dang mo cua so Frontend Next.js (Port 3000)...
start "TRAFFICGUARD FRONTEND" cmd /k ""%~dp0start_frontend.bat""
echo.
echo Da khoi dong ca 2 cua so Terminal tren man hinh!
echo Ban co the theo doi truc tiep log chay tai 2 cua so nay.
pause
