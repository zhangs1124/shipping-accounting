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

@router.get("/api/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user)
):
    """取得當前使用者未處理提醒數量"""
    count = db.query(models.Reminder).filter(
        models.Reminder.target_employee_id == current_user.id,
        models.Reminder.is_closed == 0
    ).count()
    return {"count": count}
