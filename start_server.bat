@echo off
cd /d E:\ee-invoicing
set DATABASE_URL=postgresql://postgres:OOQTkeMhuPRXJpCWuncoPgzUJNvJzdPC@crossover.proxy.rlwy.net:42492/railway
echo ============================================
echo   STARTING EE INVOICING SERVER
echo ============================================
echo.
echo Server will start on: http://localhost:8080
echo Press CTRL+C to stop the server
echo.
echo ============================================
echo.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
echo.
echo ============================================
echo Server stopped!
pause
