from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from decimal import Decimal

import models
from database import get_db

router = APIRouter(tags=["invoice_lines"])
templates = Jinja2Templates(directory="templates")


def _recalc_total(invoice: models.Invoice, db: Session):
    """重新計算帳務主項目總金額"""
    total = sum(line.subtotal for line in invoice.lines)
    invoice.total_amount = total
    db.commit()


def _check_editable(invoice: models.Invoice):
    """檢查帳務是否可編輯（草稿狀態）"""
    return invoice.status == "草稿"


@router.post("/invoices/{invoice_id}/lines")
def create_line(
    invoice_id: int,
    charge_item_id: int = Form(...),
    quantity: str = Form(...),
    unit_price: str = Form(...),
    currency: str = Form("TWD"),
    remark: str = Form(""),
    db: Session = Depends(get_db),
):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        return RedirectResponse(url="/invoices", status_code=303)

    if not _check_editable(invoice):
        return RedirectResponse(
            url=f"/invoices/{invoice_id}?error=帳務已開立，無法新增明細", status_code=303
        )

    qty = Decimal(quantity)
    price = Decimal(unit_price)
    subtotal = qty * price

    line = models.InvoiceLine(
        invoice_id=invoice_id,
        charge_item_id=charge_item_id,
        quantity=qty,
        unit_price=price,
        currency=currency,
        subtotal=subtotal,
        remark=remark,
    )
    db.add(line)
    db.flush()

    # 重新載入 invoice.lines 後計算總金額
    db.refresh(invoice)
    _recalc_total(invoice, db)

    return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)


@router.get("/invoices/{invoice_id}/lines/{line_id}/edit", response_class=HTMLResponse)
def edit_line_form(invoice_id: int, line_id: int, request: Request, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    line = db.query(models.InvoiceLine).filter(
        models.InvoiceLine.id == line_id,
        models.InvoiceLine.invoice_id == invoice_id
    ).first()

    if not invoice or not line:
        return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)

    if not _check_editable(invoice):
        return RedirectResponse(
            url=f"/invoices/{invoice_id}?error=帳務已開立，無法編輯明細", status_code=303
        )

    charge_items = db.query(models.ChargeItem).order_by(models.ChargeItem.code).all()
    return templates.TemplateResponse("invoices/edit_line.html", {
        "request": request,
        "invoice": invoice,
        "line": line,
        "charge_items": charge_items,
    })


@router.post("/invoices/{invoice_id}/lines/{line_id}/edit")
def update_line(
    invoice_id: int,
    line_id: int,
    charge_item_id: int = Form(...),
    quantity: str = Form(...),
    unit_price: str = Form(...),
    currency: str = Form("TWD"),
    remark: str = Form(""),
    db: Session = Depends(get_db),
):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    line = db.query(models.InvoiceLine).filter(
        models.InvoiceLine.id == line_id,
        models.InvoiceLine.invoice_id == invoice_id
    ).first()

    if not invoice or not line:
        return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)

    if not _check_editable(invoice):
        return RedirectResponse(
            url=f"/invoices/{invoice_id}?error=帳務已開立，無法編輯明細", status_code=303
        )

    qty = Decimal(quantity)
    price = Decimal(unit_price)
    line.charge_item_id = charge_item_id
    line.quantity = qty
    line.unit_price = price
    line.currency = currency
    line.subtotal = qty * price
    line.remark = remark
    db.flush()

    db.refresh(invoice)
    _recalc_total(invoice, db)

    return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)


@router.post("/invoices/{invoice_id}/lines/{line_id}/delete")
def delete_line(invoice_id: int, line_id: int, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    line = db.query(models.InvoiceLine).filter(
        models.InvoiceLine.id == line_id,
        models.InvoiceLine.invoice_id == invoice_id
    ).first()

    if not invoice or not line:
        return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)

    if not _check_editable(invoice):
        return RedirectResponse(
            url=f"/invoices/{invoice_id}?error=帳務已開立，無法刪除明細", status_code=303
        )

    db.delete(line)
    db.flush()

    db.refresh(invoice)
    _recalc_total(invoice, db)

    return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)
