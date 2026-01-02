# Push to GitHub Script
Write-Host "========================================"
Write-Host "Pushing to GitHub..."
Write-Host "========================================"

cd E:\EE-Invoicing

Write-Host "`n1. Checking git status..."
git status

Write-Host "`n2. Adding files..."
git add app/main.py

Write-Host "`n3. Committing..."
git commit -m "Add debugging routes and catch-all handler for Railway 404 issue"

Write-Host "`n4. Pushing to GitHub..."
git push origin main

Write-Host "`n5. Verifying push..."
git log origin/main..HEAD --oneline

Write-Host "`n========================================"
Write-Host "Done! Check GitHub to verify."
Write-Host "========================================"









