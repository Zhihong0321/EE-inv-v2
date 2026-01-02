Set-Location E:\EE-Invoicing
git add app/main.py
$commitResult = git commit -m "CRITICAL FIX: Make router imports lazy - app will start even if routers fail"
Write-Output "Commit result: $commitResult"
$pushResult = git push origin main
Write-Output "Push result: $pushResult"
git log --oneline -1 | Out-File -FilePath "last_commit.txt" -Encoding utf8
Write-Output "Done - check last_commit.txt for verification"









