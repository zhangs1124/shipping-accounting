from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

import models
from database import get_db

router = APIRouter(prefix="/customers", tags=["customers"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
def list_customers(request: Request, db: Session = Depends(get_db)):
    customers = db.query(models.Customer).order_by(models.Customer.name).all()
    return templates.TemplateResponse("customers/list.html", {
        "request": request,
        "customers": customers,
    })


@router.get("/new", response_class=HTMLResponse)
def new_customer_form(request: Request):
    return templates.TemplateResponse("customers/new.html", {
        "request": request,
        "form_data": {},
    })


@router.post("/new")
def create_customer(
    request: Request,
    name: str = Form(...),
    responsible: str = Form(""),
    invoice_prefix: str = Form("A"),
    contact: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    db: Session = Depends(get_db),
):
    existing = db.query(models.Customer).filter(models.Customer.name == name).first()
    if existing:
        return templates.TemplateResponse("customers/new.html", {
            "request": request,
            "error": f"客戶名稱 '{name}' 已存在",
            "form_data": {
                "name": name,
                "responsible": responsible,
                "invoice_prefix": invoice_prefix,
                "contact": contact,
                "phone": phone,
                "email": email,
                "address": address,
            },
        }, status_code=409)

    customer = models.Customer(
        name=name,
        responsible=responsible or None,
        invoice_prefix=invoice_prefix or "A",
        contact=contact or None,
        phone=phone or None,
        email=email or None,
        address=address or None,
    )
    db.add(customer)
    db.commit()
    return RedirectResponse(url="/customers", status_code=303)


@router.get("/{customer_id}/edit", response_class=HTMLResponse)
def edit_customer_form(customer_id: int, request: Request, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        return RedirectResponse(url="/customers", status_code=303)

    return templates.TemplateResponse("customers/edit.html", {
        "request": request,
        "customer": customer,
    })


@router.post("/{customer_id}/edit")
def update_customer(
    customer_id: int,
    request: Request,
    name: str = Form(...),
    responsible: str = Form(""),
    invoice_prefix: str = Form("A"),
    contact: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    db: Session = Depends(get_db),
):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        return RedirectResponse(url="/customers", status_code=303)

    # 名稱若變更，要避免與其他客戶重複
    other = db.query(models.Customer).filter(
        models.Customer.name == name,
        models.Customer.id != customer_id
    ).first()
    if other:
        return templates.TemplateResponse("customers/edit.html", {
            "request": request,
            "customer": customer,
            "error": f"客戶名稱 '{name}' 已存在",
        }, status_code=409)

    customer.name = name
    customer.responsible = responsible or None
    customer.invoice_prefix = invoice_prefix or "A"
    customer.contact = contact or None
    customer.phone = phone or None
    customer.email = email or None
    customer.address = address or None

    db.commit()
    return RedirectResponse(url="/customers", status_code=303)


@router.post("/api")
def api_create_customer(
    name: str = Form(...),
    responsible: str = Form(""),
    invoice_prefix: str = Form("A"),
    contact: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    db: Session = Depends(get_db),
):
    existing = db.query(models.Customer).filter(models.Customer.name == name).first()
    if existing:
        return JSONResponse({"error": f"客戶名稱 '{name}' 已存在"}, status_code=409)

    customer = models.Customer(
        name=name,
        responsible=responsible or None,
        invoice_prefix=invoice_prefix or "A",
        contact=contact or None,
        phone=phone or None,
        email=email or None,
        address=address or None,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return {
        "id": customer.id,
        "name": customer.name,
        "responsible": customer.responsible or "",
        "invoice_prefix": customer.invoice_prefix or "A",
        "contact": customer.contact or "",
        "phone": customer.phone or "",
        "email": customer.email or "",
        "address": customer.address or "",
    }


@router.post("/api/{customer_id}")
def api_update_customer(
    customer_id: int,
    name: str = Form(...),
    responsible: str = Form(""),
    invoice_prefix: str = Form("A"),
    contact: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    db: Session = Depends(get_db),
):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        return JSONResponse({"error": "客戶不存在"}, status_code=404)

    # 名稱變更檢查
    other = db.query(models.Customer).filter(
        models.Customer.name == name,
        models.Customer.id != customer_id
    ).first()
    if other:
        return JSONResponse({"error": f"客戶名稱 '{name}' 已存在"}, status_code=409)

    customer.name = name
    customer.responsible = responsible or None
    customer.invoice_prefix = invoice_prefix or "A"
    customer.contact = contact or None
    customer.phone = phone or None
    customer.email = email or None
    customer.address = address or None

    db.commit()
    db.refresh(customer)
    return {
        "id": customer.id,
        "name": customer.name,
        "responsible": customer.responsible or "",
        "invoice_prefix": customer.invoice_prefix or "A",
        "contact": customer.contact or "",
        "phone": customer.phone or "",
        "email": customer.email or "",
        "address": customer.address or "",
    }


@router.post("/api/{customer_id}/delete")
def api_delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        return JSONResponse({"error": "客戶不存在"}, status_code=404)

    # 檢查是否被帳單使用
    used_count = db.query(models.Invoice).filter(models.Invoice.customer_name == customer.name).count()
    if used_count > 0:
        return JSONResponse({"error": f"客戶已被 {used_count} 筆帳單使用，無法刪除"}, status_code=409)

    db.delete(customer)
    db.commit()
    return {"ok": True}


@router.post("/{customer_id}/delete")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    # 原有的 HTML 路由，暫時保留，但內部邏輯可導向 JSON API 或保持原樣
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        return RedirectResponse(url="/customers", status_code=303)

    used_count = db.query(models.Invoice).filter(models.Invoice.customer_name == customer.name).count()
    if used_count > 0:
        return RedirectResponse(url=f"/customers?error=客戶已被{used_count}筆帳單使用，無法刪除", status_code=303)

    db.delete(customer)
    db.commit()
    return RedirectResponse(url="/customers", status_code=303)

