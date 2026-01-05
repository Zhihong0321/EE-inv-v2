@echo off
cd /d E:\EE-Invoicing
echo ========================================
echo Pushing to GitHub...
echo ========================================
echo.
echo Current status:
git status --short
echo.
echo Adding files...
git add app/main.py
echo.
echo Committing...
git commit -m "CRITICAL FIX: Make router imports lazy - app will start even if routers fail"
echo.
echo Pushing to GitHub...
git push origin main
echo.
echo ========================================
echo Done! Check GitHub to verify.
echo ========================================
pause














