from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from utils.templates import templates
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

import models
from database import get_db

router = APIRouter(prefix="/task-categories", tags=["task_categories"])

@router.get("", response_class=HTMLResponse)
def list_task_categories(request: Request, db: Session = Depends(get_db)):
    """
    列出所有進出港項目基本檔。
    """
    categories = db.query(models.TaskCategory).order_by(models.TaskCategory.display_order, models.TaskCategory.task_group).all()
    return templates.TemplateResponse("task_categories/list.html", {"request": request, "categories": categories})

@router.post("/api")
def api_create_category(
    name: str = Form(...),
    task_group: str = Form(...),
    default_fee: Decimal = Form(0),
    display_order: int = Form(0),
    base_milestone: Optional[str] = Form(None),
    expected_offset_hours: int = Form(0),
    db: Session = Depends(get_db),
):
    """
    新增任務項目。
    """
    category = models.TaskCategory(
        name=name,
        task_group=task_group,
        default_fee=default_fee,
        display_order=display_order,
        base_milestone=base_milestone,
        expected_offset_hours=expected_offset_hours,
        is_active=1
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return JSONResponse({
        "id": category.id,
        "name": category.name,
        "task_group": category.task_group,
        "default_fee": float(category.default_fee),
        "display_order": category.display_order,
        "base_milestone": category.base_milestone,
        "expected_offset_hours": category.expected_offset_hours,
        "is_active": category.is_active
    })

@router.post("/api/{cat_id}")
def api_update_category(
    cat_id: int,
    name: str = Form(...),
    task_group: str = Form(...),
    default_fee: Decimal = Form(0),
    display_order: int = Form(0),
    is_active: int = Form(1),
    base_milestone: Optional[str] = Form(None),
    expected_offset_hours: int = Form(0),
    db: Session = Depends(get_db),
):
    """
    更新任務項目。
    """
    category = db.query(models.TaskCategory).filter(models.TaskCategory.id == cat_id).first()
    if not category:
        return JSONResponse({"error": "項目不存在"}, status_code=404)
    category.name = name
    category.task_group = task_group
    category.default_fee = default_fee
    category.display_order = display_order
    category.is_active = is_active
    category.base_milestone = base_milestone
    category.expected_offset_hours = expected_offset_hours
    db.commit()
    return JSONResponse({
        "id": category.id,
        "name": category.name,
        "task_group": category.task_group,
        "default_fee": float(category.default_fee),
        "display_order": category.display_order,
        "base_milestone": category.base_milestone,
        "expected_offset_hours": category.expected_offset_hours,
        "is_active": category.is_active
    })

@router.post("/api/{cat_id}/delete")
def api_delete_category(cat_id: int, db: Session = Depends(get_db)):
    """
    刪除檢疫項目。若已有執行紀錄則禁止刪除。
    """
    category = db.query(models.TaskCategory).filter(models.TaskCategory.id == cat_id).first()
    if not category:
        return JSONResponse({"error": "項目不存在"}, status_code=404)
    
    # 檢查是否有日誌紀錄
    if db.query(models.VoyageTaskLog).filter(models.VoyageTaskLog.task_id == cat_id).count() > 0:
        return JSONResponse({"error": "此項目已有執行紀錄，無法刪除。建議將其設為停用。"}, status_code=409)
        
    db.delete(category)
    db.commit()
    return JSONResponse({"ok": True})
