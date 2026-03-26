from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from utils.templates import templates
from database import get_db
import models
from utils.auth import get_current_user, check_permissions, get_password_hash

router = APIRouter(prefix="/employees", tags=["employees"])

# 權限檢查：僅限管理員
admin_dependency = Depends(check_permissions(["admin"]))

@router.get("", response_class=HTMLResponse)
def list_employees(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
    _ = admin_dependency
):
    # 預載入部門與角色
    employees = db.query(models.Employee).options(
        joinedload(models.Employee.department),
        joinedload(models.Employee.role)
    ).order_by(models.Employee.username).all()
    
    return templates.TemplateResponse("employees/list.html", {
        "request": request,
        "employees": employees,
        "current_user": current_user
    })

@router.get("/new", response_class=HTMLResponse)
def new_employee_form(
    request: Request,
    db: Session = Depends(get_db),
    _ = admin_dependency
):
    departments = db.query(models.Department).all()
    roles = db.query(models.Role).all()
    return templates.TemplateResponse("employees/edit.html", {
        "request": request,
        "employee": None,
        "departments": departments,
        "roles": roles
    })

@router.post("/new")
def create_employee(
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(""),
    department_id: int = Form(...),
    role_id: int = Form(...),
    db: Session = Depends(get_db),
    _ = admin_dependency
):
    if db.query(models.Employee).filter(models.Employee.username == username).first():
        # 這裡簡單處理，實際可用 Flash Message 或傳回頁面顯示錯誤
        raise HTTPException(status_code=400, detail="帳號已存在")
    
    emp = models.Employee(
        username=username,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        email=email,
        department_id=department_id,
        role_id=role_id,
        is_active=1
    )
    db.add(emp)
    db.commit()
    return RedirectResponse(url="/employees", status_code=303)

@router.get("/{emp_id}/edit", response_class=HTMLResponse)
def edit_employee_form(
    emp_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _ = admin_dependency
):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        return RedirectResponse(url="/employees", status_code=303)
    
    departments = db.query(models.Department).all()
    roles = db.query(models.Role).all()
    return templates.TemplateResponse("employees/edit.html", {
        "request": request,
        "employee": emp,
        "departments": departments,
        "roles": roles
    })

@router.post("/{emp_id}/edit")
def update_employee(
    emp_id: int,
    full_name: str = Form(...),
    email: str = Form(""),
    department_id: int = Form(...),
    role_id: int = Form(...),
    password: str = Form(None), # 若有填寫則修改密碼
    is_active: int = Form(1),
    db: Session = Depends(get_db),
    _ = admin_dependency
):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="員工不存在")
    
    emp.full_name = full_name
    emp.email = email
    emp.department_id = department_id
    emp.role_id = role_id
    emp.is_active = is_active
    
    if password and password.strip():
        emp.hashed_password = get_password_hash(password)
        
    db.commit()
    return RedirectResponse(url="/employees", status_code=303)

@router.post("/{emp_id}/toggle")
def toggle_employee_status(
    emp_id: int,
    db: Session = Depends(get_db),
    _ = admin_dependency
):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        return JSONResponse({"error": "員工不存在"}, status_code=404)
    
    emp.is_active = 0 if emp.is_active == 1 else 1
    db.commit()
    return JSONResponse({"ok": True, "is_active": emp.is_active})
