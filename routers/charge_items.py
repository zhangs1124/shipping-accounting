from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from decimal import Decimal

import models
from database import get_db

router = APIRouter(prefix="/charge-items", tags=["charge_items"])
templates = Jinja2Templates(directory="templates")

CURRENCIES = ["TWD", "USD", "EUR", "JPY", "CNY", "HKD"]


@router.get("", response_class=HTMLResponse)
def list_charge_items(request: Request, db: Session = Depends(get_db)):
    items = db.query(models.ChargeItem).order_by(models.ChargeItem.code).all()
    return templates.TemplateResponse("charge_items/list.html", {
        "request": request,
        "items": items,
        "currencies": CURRENCIES,
    })


@router.post("")
def create_charge_item(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    currency: str = Form("TWD"),
    default_unit_price: str = Form("0"),
    db: Session = Depends(get_db),
):
    existing = db.query(models.ChargeItem).filter(models.ChargeItem.code == code).first()
    if existing:
        items = db.query(models.ChargeItem).order_by(models.ChargeItem.code).all()
        return templates.TemplateResponse("charge_items/list.html", {
            "request": request,
            "items": items,
            "currencies": CURRENCIES,
            "error": f"收費項目代碼 '{code}' 已存在",
            "form_data": {"code": code, "name": name, "currency": currency,
                          "default_unit_price": default_unit_price},
        }, status_code=409)

    item = models.ChargeItem(
        code=code,
        name=name,
        currency=currency,
        default_unit_price=Decimal(default_unit_price or "0"),
    )
    db.add(item)
    db.commit()
    return RedirectResponse(url="/charge-items", status_code=303)


@router.get("/{item_id}/edit", response_class=HTMLResponse)
def edit_charge_item_form(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.query(models.ChargeItem).filter(models.ChargeItem.id == item_id).first()
    if not item:
        return RedirectResponse(url="/charge-items", status_code=303)
    return templates.TemplateResponse("charge_items/edit.html", {
        "request": request,
        "item": item,
        "currencies": CURRENCIES,
    })


@router.post("/{item_id}/edit")
def update_charge_item(
    item_id: int,
    name: str = Form(...),
    currency: str = Form("TWD"),
    default_unit_price: str = Form("0"),
    db: Session = Depends(get_db),
):
    item = db.query(models.ChargeItem).filter(models.ChargeItem.id == item_id).first()
    if not item:
        return RedirectResponse(url="/charge-items", status_code=303)

    item.name = name
    item.currency = currency
    item.default_unit_price = Decimal(default_unit_price or "0")
    db.commit()
    return RedirectResponse(url="/charge-items", status_code=303)


@router.post("/{item_id}/delete")
def delete_charge_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.ChargeItem).filter(models.ChargeItem.id == item_id).first()
    if not item:
        return RedirectResponse(url="/charge-items", status_code=303)

    line_count = db.query(models.InvoiceLine).filter(
        models.InvoiceLine.charge_item_id == item_id
    ).count()
    if line_count > 0:
        return RedirectResponse(
            url="/charge-items?error=收費項目已被帳務明細使用，無法刪除", status_code=303
        )

    db.delete(item)
    db.commit()
    return RedirectResponse(url="/charge-items", status_code=303)


# ── JSON API（供 Modal 使用）──────────────────────

def _item_json(item):
    return {
        "id": item.id, "code": item.code, "name": item.name,
        "currency": item.currency,
        "default_unit_price": str(item.default_unit_price),
    }


@router.post("/api")
def api_create_charge_item(
    code: str = Form(...),
    name: str = Form(...),
    currency: str = Form("TWD"),
    default_unit_price: str = Form("0"),
    db: Session = Depends(get_db),
):
    if db.query(models.ChargeItem).filter(models.ChargeItem.code == code).first():
        return JSONResponse({"error": f"收費項目代碼 '{code}' 已存在"}, status_code=409)
    item = models.ChargeItem(
        code=code, name=name, currency=currency,
        default_unit_price=Decimal(default_unit_price or "0"),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return JSONResponse(_item_json(item))


@router.post("/api/{item_id}")
def api_update_charge_item(
    item_id: int,
    name: str = Form(...),
    currency: str = Form("TWD"),
    default_unit_price: str = Form("0"),
    db: Session = Depends(get_db),
):
    item = db.query(models.ChargeItem).filter(models.ChargeItem.id == item_id).first()
    if not item:
        return JSONResponse({"error": "收費項目不存在"}, status_code=404)
    item.name = name
    item.currency = currency
    item.default_unit_price = Decimal(default_unit_price or "0")
    db.commit()
    return JSONResponse(_item_json(item))


@router.post("/api/{item_id}/delete")
def api_delete_charge_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.ChargeItem).filter(models.ChargeItem.id == item_id).first()
    if not item:
        return JSONResponse({"error": "收費項目不存在"}, status_code=404)
    if db.query(models.InvoiceLine).filter(models.InvoiceLine.charge_item_id == item_id).count() > 0:
        return JSONResponse({"error": "收費項目已被帳務明細使用，無法刪除"}, status_code=409)
    db.delete(item)
    db.commit()
    return JSONResponse({"ok": True})
