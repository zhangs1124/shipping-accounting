from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from utils.templates import templates
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Optional

import models
from database import get_db
from utils.auth import get_current_user

router = APIRouter(prefix="/reminders", tags=["reminders"])

@router.get("", response_class=HTMLResponse)
def list_reminders(
    request: Request, 
    filter_user: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user)
):
    """提醒中心清單頁面"""
    now = datetime.now()
    query = db.query(models.Reminder).options(
        joinedload(models.Reminder.target_employee)
    ).filter(models.Reminder.is_closed == 0)
    
    # 權限控管：非 Admin 僅能看自己的提醒
    is_admin = current_user.role and current_user.role.name == "Admin"
    
    if not is_admin:
        query = query.filter(models.Reminder.target_employee_id == current_user.id)
    elif filter_user:
        query = query.filter(models.Reminder.target_employee_id == filter_user)

    reminders = query.order_by(models.Reminder.created_at.desc()).all()
    
    # 取得所有員工名單供 Admin 篩選
    employees = []
    if is_admin:
        employees = db.query(models.Employee).filter(models.Employee.is_active == 1).all()

    return templates.TemplateResponse("reminders/list.html", {
        "request": request,
        "reminders": reminders,
        "current_user": current_user,
        "is_admin": is_admin,
        "employees": employees,
        "filter_user": filter_user
    })

@router.post("/close/{reminder_id}")
def close_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user)
):
    """結案單筆提醒"""
    reminder = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
    if not reminder:
        return JSONResponse({"error": "提醒不存在"}, status_code=404)
        
    # 權限檢查：僅本人或 Admin 可結案
    is_admin = current_user.role and current_user.role.name == "Admin"
    if not is_admin and reminder.target_employee_id != current_user.id:
        return JSONResponse({"error": "權限不足"}, status_code=403)

    reminder.is_closed = 1
    reminder.updated_at = datetime.now()
    db.commit()
    
    return RedirectResponse(url="/reminders", status_code=303)

@router.post("/send/{reminder_id}")
def send_reminder_now(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user)
):
    """手動立即觸發提醒信件"""
    from utils.mailer import send_email
    reminder = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
    if not reminder:
        return JSONResponse({"error": "提醒不存在"}, status_code=404)
        
    is_admin = current_user.role and current_user.role.name == "Admin"
    if not is_admin and reminder.target_employee_id != current_user.id:
        return JSONResponse({"error": "權限不足"}, status_code=403)

    recipients = {"zhangj1124@gmail.com"}
    if reminder.target_employee and reminder.target_employee.email:
        recipients.add(reminder.target_employee.email)
        
    for recp in recipients:
        try:
            html_content = f"""
            <html>
            <body>
                <h2>中央提醒中心 - 手動立即傳送</h2>
                <p><strong>標題：</strong> {reminder.title}</p>
                <p><strong>內容：</strong> {reminder.content}</p>
                <p><strong>負責人員 ID：</strong> {reminder.target_employee_id}</p>
                <hr>
                <p>此任務尚未完成，此為手動觸發的提醒信件。</p>
            </body>
            </html>
            """
            send_email(
                subject=f"[立即傳送] {reminder.title}",
                html_content=html_content,
                recipient=recp
            )
            from utils.audit_logger import log_action
            log_action(
                db, 
                action="SEND_EMAIL", 
                table_name="reminders", 
                target_id=str(reminder.id),
                new_value={"recipient": recp, "title": reminder.title, "manual": True},
                user_id=current_user.id
            )
        except Exception as email_err:
            print(f"立即傳送失敗給 {recp}: {email_err}")
            
    return RedirectResponse(url="/reminders", status_code=303)

@router.get("/api/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user)
):
    """取得當前使用者未處理提醒數量"""
    now = datetime.now()
    count = db.query(models.Reminder).filter(
        models.Reminder.target_employee_id == current_user.id,
        models.Reminder.is_closed == 0,
        (models.Reminder.next_remind_at == None) | (models.Reminder.next_remind_at <= now)
    ).count()
    return {"count": count}

@router.post("/api/manual")
def add_manual_reminder(
    voyage_task_log_id: int = Form(...),
    remind_at: str = Form(...),
    frequency: str = Form("ONCE"),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user)
):
    """手動在進出港任務頁面加入自訂提醒"""
    from datetime import datetime
    try:
        dt_remind = datetime.fromisoformat(remind_at.replace("T", " "))
    except ValueError:
        return JSONResponse({"error": "時間格式錯誤"}, status_code=400)
        
    # 尋找對應的 VoyageTaskLog，確保資料存在，並取得相關細節
    log = db.query(models.VoyageTaskLog).filter(models.VoyageTaskLog.id == voyage_task_log_id).first()
    if not log:
        return JSONResponse({"error": "找不到該任務紀錄"}, status_code=404)
        
    voyage = log.voyage
    category = log.task_category
    
    # 決定發送對象：優先使用航次操作員，若無則為當前設定者
    target_emp_id = voyage.operator_id if voyage.operator_id else current_user.id

    freq_map = {
        "ONCE": "單次",
        "DAILY": "每天",
        "HOURLY": "每小時",
        "MINUTELY": "每分鐘"
    }
    freq_label = freq_map.get(frequency, "自訂")
    
    new_reminder = models.Reminder(
        title=f"自訂提醒 ({freq_label})：{voyage.voyage_no} - {category.name}",
        content=f"使用者 {current_user.full_name or current_user.username} 針對航次 {voyage.voyage_no} 的「{category.name}」設定了自訂關切排程，提醒時間到了！",
        remind_type="MANUAL_TASK",
        source_table="voyage_task_logs",
        source_id=log.id,
        target_employee_id=target_emp_id,
        deadline=dt_remind,
        frequency=frequency,
        next_remind_at=dt_remind
    )
    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)
    
    return {"status": "success", "message": "已成功加入提醒中心排程"}

