@echo off
echo Starting Shipping Accounting System...
@echo off
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
