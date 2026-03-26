from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

import models
from database import engine
from routers import ships, voyages, charge_items, invoices, invoice_lines, customers, voyage_tasks, task_categories
from apscheduler.schedulers.background import BackgroundScheduler
from tasks.email_tasks import check_and_send_reminders

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
    scheduler.add_job(check_and_send_reminders, 'cron', hour=1, minute=0, id="daily_check")
    # 2. 每小時整點再次檢查
    scheduler.add_job(check_and_send_reminders, 'cron', hour='*', minute=0, id="hourly_check")
    # 3. 測試用：每 2 分鐘檢查一次
    scheduler.add_job(check_and_send_reminders, 'interval', minutes=2, id="test_check")
    
    if not scheduler.running:
        scheduler.start()
        print(f">>> [系統訊息] 自動提醒排程已啟動。目前時間: {datetime.now()}")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 掛載路由
app.include_router(ships.router)
app.include_router(voyages.router)
app.include_router(charge_items.router)
app.include_router(invoices.router)
app.include_router(invoice_lines.router)
app.include_router(customers.router)
app.include_router(voyage_tasks.router)
app.include_router(task_categories.router)


@app.get("/")
def root():
    return RedirectResponse(url="/invoices")


@app.get("/tasks/trigger-reminders")
def trigger_reminders():
    # 手動觸發任務以供測試
    check_and_send_reminders()
    return {"message": "已手動觸發逾期提醒檢查任務，請查看伺服器日誌或信箱。"}
