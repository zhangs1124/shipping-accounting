@echo off
echo Starting Shipping Accounting System...
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
