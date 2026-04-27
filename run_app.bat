@echo off
chcp 65001
echo ========================================
echo   Starting Shipping System (10.2.4.15:8001)
echo ========================================
python -m uvicorn main:app --host 10.2.4.15 --port 8001
pause
