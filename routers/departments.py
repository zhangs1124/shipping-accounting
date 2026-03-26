from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from utils.templates import templates
from database import get_db
import models
from utils.auth import get_current_user, check_permissions

router = APIRouter(prefix="/departments", tags=["departments"])

# 權限檢查：僅限管理員
admin_dependency = Depends(check_permissions(["admin"]))

@router.get("", response_class=HTMLResponse)
def list_departments(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
    _ = admin_dependency
):
    departments = db.query(models.Department).order_by(models.Department.id).all()
    return templates.TemplateResponse("departments/list.html", {
        "request": request,
        "departments": departments,
        "current_user": current_user
    })

@router.post("/api")
def api_create_department(
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    _ = admin_dependency
):
    if db.query(models.Department).filter(models.Department.name == name).first():
        return JSONResponse({"error": f"部門名稱 '{name}' 已存在"}, status_code=409)
    
    dept = models.Department(name=name, description=description)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return JSONResponse({
        "id": dept.id,
        "name": dept.name,
        "description": dept.description or ""
    })

@router.post("/api/{dept_id}/edit")
def api_update_department(
    dept_id: int,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    _ = admin_dependency
):
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept:
        return JSONResponse({"error": "部門不存在"}, status_code=404)
    
    # 名稱重複檢查
    other = db.query(models.Department).filter(models.Department.name == name, models.Department.id != dept_id).first()
    if other:
        return JSONResponse({"error": f"部門名稱 '{name}' 已存在"}, status_code=409)
    
    dept.name = name
    dept.description = description
    db.commit()
    return JSONResponse({"id": dept.id, "name": dept.name, "description": dept.description})

@router.post("/api/{dept_id}/delete")
def api_delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    _ = admin_dependency
):
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept:
        return JSONResponse({"error": "部門不存在"}, status_code=404)
    
    # 檢查是否還有員工
    if db.query(models.Employee).filter(models.Employee.department_id == dept_id).count() > 0:
        return JSONResponse({"error": "該部門內仍有員工，無法刪除。"}, status_code=400)
    
    db.delete(dept)
    db.commit()
    return JSONResponse({"ok": True})
