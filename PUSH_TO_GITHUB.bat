@echo off
echo ========================================
echo Pushing Critical Fix to GitHub
echo ========================================
echo.

cd /d E:\EE-Invoicing

echo [1/4] Checking git status...
git status --short
echo.

echo [2/4] Staging app/main.py...
git add app/main.py
if %ERRORLEVEL% EQU 0 (
    echo ✓ File staged successfully
) else (
    echo ✗ Error staging file
    pause
    exit /b 1
)
echo.

echo [3/4] Committing changes...
git commit -m "CRITICAL FIX: Make router imports lazy - app will start even if routers fail"
if %ERRORLEVEL% EQU 0 (
    echo ✓ Commit successful
) else (
    echo ✗ Commit failed (might be nothing to commit)
)
echo.

echo [4/4] Pushing to GitHub...
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo ✓ Push successful!
) else (
    echo ✗ Push failed
    pause
    exit /b 1
)
echo.

echo ========================================
echo Latest commit:
git log --oneline -1
echo ========================================
echo.
echo Done! Check GitHub to verify the push.
pause







