from fastapi import FastAPI, Request, status, Depends
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

import os
from jose import jwt, JWTError
from sqlalchemy.orm import joinedload
import models
from database import engine, SessionLocal
from routers import auth, ships, voyages, charge_items, invoices, invoice_lines, customers, voyage_tasks, task_categories
from apscheduler.schedulers.background import BackgroundScheduler
from tasks.invoice_reminders import check_overdue_invoices
from utils.auth import get_current_user, check_permissions
from utils.templates import templates

# 建立所有資料表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="船務部帳務系統")

# ────────────────────────────────────────────────────────────
#  排程器設定 (APScheduler)
# ────────────────────────────────────────────────────────────
scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    print(">>> [系統訊息] 正在初始化背景任務排程器...")
    
    # 1. 每天凌晨 01:00 檢查逾期帳單
    scheduler.add_job(check_overdue_invoices, 'cron', hour=1, minute=0, id="daily_check")
    # 2. 每小時整點再次檢查
    scheduler.add_job(check_overdue_invoices, 'cron', hour='*', minute=0, id="hourly_check")
    # 3. 測試用：每 2 分鐘檢查一次
    scheduler.add_job(check_overdue_invoices, 'interval', minutes=2, id="test_check")
    
    if not scheduler.running:
        scheduler.start()
        print(f">>> [系統訊息] 自動提醒排程已啟動。目前時間: {datetime.now()}")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

@app.middleware("http")
async def add_user_to_request(request: Request, call_next):
    token = request.cookies.get("access_token")
    request.state.user = None
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username:
                db = SessionLocal()
                # 使用 joinedload 預先載入角色與部門資訊，避免 DetachedInstanceError
                user = db.query(models.Employee).options(
                    joinedload(models.Employee.role),
                    joinedload(models.Employee.department)
                ).filter(models.Employee.username == username).first()
                if user and user.is_active:
                    request.state.user = user
                db.close()
        except (JWTError, Exception):
            pass
    response = await call_next(request)
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")
# templates 已從 utils.templates 匯入

# 掛載路由
app.include_router(auth.router)
# 以下路由皆需登入後才可存取
app.include_router(ships.router, dependencies=[Depends(get_current_user)])
app.include_router(voyages.router, dependencies=[Depends(get_current_user)])
app.include_router(charge_items.router, dependencies=[Depends(get_current_user)])
app.include_router(invoices.router, dependencies=[Depends(get_current_user)])
app.include_router(invoice_lines.router, dependencies=[Depends(get_current_user)])
app.include_router(customers.router, dependencies=[Depends(get_current_user)])
app.include_router(voyage_tasks.router, dependencies=[Depends(get_current_user)])
app.include_router(task_categories.router, dependencies=[Depends(get_current_user)])


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_exception_handler(request: Request, exc: Exception):
    return RedirectResponse(url="/login")


@app.get("/")
def root():
    return RedirectResponse(url="/invoices")


@app.get("/tasks/trigger-reminders")
def trigger_reminders():
    # 手動觸發任務以供測試
    check_overdue_invoices()
    return {"message": "已手動觸發逾期提醒檢查任務，請查看伺服器日誌或信箱。"}
