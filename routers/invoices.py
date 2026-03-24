from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import date
import csv
import io
import re

import models
from database import get_db

router = APIRouter(prefix="/invoices", tags=["invoices"])
templates = Jinja2Templates(directory="templates")

INVOICE_STATUSES = ["草稿", "已開立", "已收款"]


def generate_invoice_no(db: Session, invoice_date: date) -> str:
    prefix = f"A{invoice_date.strftime('%Y%m%d')}-"
    pattern = re.compile(rf"^A{invoice_date.strftime('%Y%m%d')}\-(\d{{3}})$")
    existing_nos = (
        db.query(models.Invoice.invoice_no)
        .filter(models.Invoice.invoice_no.like(f"{prefix}%"))
        .all()
    )

    max_seq = 0
    for (invoice_no,) in existing_nos:
        m = pattern.match(invoice_no)
        if m:
            max_seq = max(max_seq, int(m.group(1)))
    return f"{prefix}{max_seq + 1:03d}"


@router.get("", response_class=HTMLResponse)
def list_invoices(
    request: Request,
    voyage_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Invoice)
    if voyage_id:
        query = query.filter(models.Invoice.voyage_id == voyage_id)
    if status:
        query = query.filter(models.Invoice.status == status)
    if date_from:
        query = query.filter(models.Invoice.invoice_date >= date.fromisoformat(date_from))
    if date_to:
        query = query.filter(models.Invoice.invoice_date <= date.fromisoformat(date_to))

    invoices = query.order_by(models.Invoice.invoice_date.desc()).all()
    voyages = db.query(models.Voyage).order_by(models.Voyage.voyage_no).all()

    return templates.TemplateResponse("invoices/list.html", {
        "request": request,
        "invoices": invoices,
        "voyages": voyages,
        "statuses": INVOICE_STATUSES,
        "filter": {
            "voyage_id": voyage_id,
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
        },
    })


@router.get("/new", response_class=HTMLResponse)
def new_invoice_form(request: Request, db: Session = Depends(get_db)):
    voyages = db.query(models.Voyage).order_by(models.Voyage.voyage_no).all()
    today = date.today()
    return templates.TemplateResponse("invoices/new.html", {
        "request": request,
        "voyages": voyages,
        "suggested_invoice_no": generate_invoice_no(db, today),
        "today_str": today.isoformat(),
    })


@router.post("")
def create_invoice(
    request: Request,
    voyage_id: int = Form(...),
    customer_name: str = Form(...),
    invoice_date: str = Form(...),
    db: Session = Depends(get_db),
):
    invoice_dt = date.fromisoformat(invoice_date)
    for _ in range(5):
        invoice_no = generate_invoice_no(db, invoice_dt)
        invoice = models.Invoice(
            invoice_no=invoice_no,
            voyage_id=voyage_id,
            customer_name=customer_name,
            invoice_date=invoice_dt,
            status="草稿",
            total_amount=0,
        )
        db.add(invoice)
        try:
            db.commit()
            db.refresh(invoice)
            return RedirectResponse(url=f"/invoices/{invoice.id}", status_code=303)
        except IntegrityError:
            # Unique key collision can happen when multiple users create at the same time.
            db.rollback()
            continue

    voyages = db.query(models.Voyage).order_by(models.Voyage.voyage_no).all()
    return templates.TemplateResponse("invoices/new.html", {
        "request": request,
        "voyages": voyages,
        "error": "系統忙碌中，請稍後重試建立帳單",
        "form_data": {
            "voyage_id": voyage_id,
            "customer_name": customer_name,
            "invoice_date": invoice_date,
        },
        "suggested_invoice_no": generate_invoice_no(db, invoice_dt),
        "today_str": date.today().isoformat(),
    }, status_code=409)


@router.get("/{invoice_id}", response_class=HTMLResponse)
def invoice_detail(invoice_id: int, request: Request, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        return RedirectResponse(url="/invoices", status_code=303)

    charge_items = db.query(models.ChargeItem).order_by(models.ChargeItem.code).all()
    return templates.TemplateResponse("invoices/detail.html", {
        "request": request,
        "invoice": invoice,
        "charge_items": charge_items,
        "statuses": INVOICE_STATUSES,
        "can_edit": invoice.status == "草稿",
    })


@router.post("/{invoice_id}/status")
def update_invoice_status(
    invoice_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        return RedirectResponse(url="/invoices", status_code=303)

    if status in INVOICE_STATUSES:
        invoice.status = status
        db.commit()
    return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)


@router.get("/{invoice_id}/print", response_class=HTMLResponse)
def print_invoice(invoice_id: int, request: Request, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        return RedirectResponse(url="/invoices", status_code=303)
    return templates.TemplateResponse("invoices/print.html", {
        "request": request,
        "invoice": invoice,
    })


@router.get("/{invoice_id}/export-csv")
def export_csv(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        return RedirectResponse(url="/invoices", status_code=303)

    output = io.StringIO()
    writer = csv.writer(output)

    # 標頭資訊
    writer.writerow(["帳單編號", invoice.invoice_no])
    writer.writerow(["客戶名稱", invoice.customer_name])
    writer.writerow(["帳單日期", invoice.invoice_date.strftime("%Y-%m-%d")])
    writer.writerow(["航次編號", invoice.voyage.voyage_no])
    writer.writerow(["船舶", f"{invoice.voyage.ship.code} - {invoice.voyage.ship.name}"])
    writer.writerow(["狀態", invoice.status])
    writer.writerow([])

    # 明細標題
    writer.writerow(["項目代碼", "項目名稱", "數量", "單價", "幣別", "小計", "備註"])
    for line in invoice.lines:
        writer.writerow([
            line.charge_item.code,
            line.charge_item.name,
            float(line.quantity),
            float(line.unit_price),
            line.currency,
            float(line.subtotal),
            line.remark or "",
        ])
    writer.writerow([])
    writer.writerow(["", "", "", "", "總計", float(invoice.total_amount), ""])

    output.seek(0)
    filename = f"invoice_{invoice.invoice_no}.csv"
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
