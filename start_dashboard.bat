@echo off
title Keday70 Dashboard Launcher

echo ==============================================
echo    MENYALAKAN KEDAY70 BI DASHBOARD
echo ==============================================
echo.

:: Set PYTHONPATH agar import dari root terbaca
set PYTHONPATH=%cd%

echo [1/2] Menyalakan Backend FastAPI...
start cmd /k "title Keday70 Backend && uvicorn backend.main:app --port 8000 --reload"

echo [2/2] Menyalakan Frontend Vue 3...
start cmd /k "title Keday70 Frontend && cd frontend_vue && npm run dev"

echo.
echo Selesai! Server sedang dijalankan.
echo Silakan periksa jendela Terminal Vue Frontend untuk melihat alamat URL lokal Anda (misal: http://localhost:5173).
echo.
pause
