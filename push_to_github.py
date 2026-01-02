#!/usr/bin/env python3
import subprocess
import sys
import os

os.chdir(r'E:\EE-Invoicing')

print("=" * 60)
print("Pushing to GitHub...")
print("=" * 60)

# Check status
print("\n1. Checking git status...")
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)

# Add file
print("\n2. Adding app/main.py...")
result = subprocess.run(['git', 'add', 'app/main.py'], capture_output=True, text=True)
if result.returncode == 0:
    print("✓ File staged")
else:
    print("✗ Error:", result.stderr)

# Commit
print("\n3. Committing...")
result = subprocess.run(['git', 'commit', '-m', 'CRITICAL FIX: Make router imports lazy - app will start even if routers fail'], capture_output=True, text=True)
print(result.stdout)
if result.stderr and 'nothing to commit' not in result.stderr.lower():
    print("Errors:", result.stderr)

# Push
print("\n4. Pushing to GitHub...")
result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)

# Verify
print("\n5. Latest commit:")
result = subprocess.run(['git', 'log', '--oneline', '-1'], capture_output=True, text=True)
print(result.stdout)

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)









