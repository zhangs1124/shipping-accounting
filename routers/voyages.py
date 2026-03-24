from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

import models
from database import get_db

router = APIRouter(prefix="/voyages", tags=["voyages"])
templates = Jinja2Templates(directory="templates")

VOYAGE_STATUSES = ["計畫中", "進行中", "已完成"]


@router.get("", response_class=HTMLResponse)
def list_voyages(request: Request, db: Session = Depends(get_db)):
    voyages = db.query(models.Voyage).order_by(models.Voyage.voyage_no).all()
    ships = db.query(models.Ship).order_by(models.Ship.code).all()
    return templates.TemplateResponse("voyages/list.html", {
        "request": request,
        "voyages": voyages,
        "ships": ships,
        "statuses": VOYAGE_STATUSES,
    })


@router.post("")
def create_voyage(
    request: Request,
    voyage_no: str = Form(...),
    ship_id: int = Form(...),
    port_of_loading: str = Form(""),
    port_of_discharge: str = Form(""),
    etd: Optional[str] = Form(None),
    eta: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    existing = db.query(models.Voyage).filter(models.Voyage.voyage_no == voyage_no).first()
    if existing:
        voyages = db.query(models.Voyage).order_by(models.Voyage.voyage_no).all()
        ships = db.query(models.Ship).order_by(models.Ship.code).all()
        return templates.TemplateResponse("voyages/list.html", {
            "request": request,
            "voyages": voyages,
            "ships": ships,
            "statuses": VOYAGE_STATUSES,
            "error": f"航次編號 '{voyage_no}' 已存在",
            "form_data": {
                "voyage_no": voyage_no, "ship_id": ship_id,
                "port_of_loading": port_of_loading, "port_of_discharge": port_of_discharge,
                "etd": etd, "eta": eta,
            },
        }, status_code=409)

    from datetime import date
    voyage = models.Voyage(
        voyage_no=voyage_no,
        ship_id=ship_id,
        port_of_loading=port_of_loading,
        port_of_discharge=port_of_discharge,
        etd=date.fromisoformat(etd) if etd else None,
        eta=date.fromisoformat(eta) if eta else None,
        status="計畫中",
    )
    db.add(voyage)
    db.commit()
    return RedirectResponse(url="/voyages", status_code=303)


@router.get("/{voyage_id}/edit", response_class=HTMLResponse)
def edit_voyage_form(voyage_id: int, request: Request, db: Session = Depends(get_db)):
    voyage = db.query(models.Voyage).filter(models.Voyage.id == voyage_id).first()
    if not voyage:
        return RedirectResponse(url="/voyages", status_code=303)
    ships = db.query(models.Ship).order_by(models.Ship.code).all()
    return templates.TemplateResponse("voyages/edit.html", {
        "request": request,
        "voyage": voyage,
        "ships": ships,
        "statuses": VOYAGE_STATUSES,
    })


@router.post("/{voyage_id}/edit")
def update_voyage(
    voyage_id: int,
    ship_id: int = Form(...),
    port_of_loading: str = Form(""),
    port_of_discharge: str = Form(""),
    etd: Optional[str] = Form(None),
    eta: Optional[str] = Form(None),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    voyage = db.query(models.Voyage).filter(models.Voyage.id == voyage_id).first()
    if not voyage:
        return RedirectResponse(url="/voyages", status_code=303)

    from datetime import date
    voyage.ship_id = ship_id
    voyage.port_of_loading = port_of_loading
    voyage.port_of_discharge = port_of_discharge
    voyage.etd = date.fromisoformat(etd) if etd else None
    voyage.eta = date.fromisoformat(eta) if eta else None
    voyage.status = status
    db.commit()
    return RedirectResponse(url="/voyages", status_code=303)


@router.post("/{voyage_id}/delete")
def delete_voyage(voyage_id: int, db: Session = Depends(get_db)):
    voyage = db.query(models.Voyage).filter(models.Voyage.id == voyage_id).first()
    if not voyage:
        return RedirectResponse(url="/voyages", status_code=303)

    invoice_count = db.query(models.Invoice).filter(models.Invoice.voyage_id == voyage_id).count()
    if invoice_count > 0:
        return RedirectResponse(url="/voyages?error=航次已有關聯帳務，無法刪除", status_code=303)

    db.delete(voyage)
    db.commit()
    return RedirectResponse(url="/voyages", status_code=303)


# ── JSON API（供 Modal 使用）──────────────────────

def _voyage_json(v):
    return {
        "id": v.id, "voyage_no": v.voyage_no, "ship_id": v.ship_id,
        "port_of_loading": v.port_of_loading or "",
        "port_of_discharge": v.port_of_discharge or "",
        "etd": v.etd.isoformat() if v.etd else "",
        "eta": v.eta.isoformat() if v.eta else "",
        "status": v.status,
    }


@router.post("/api")
def api_create_voyage(
    voyage_no: str = Form(...),
    ship_id: int = Form(...),
    port_of_loading: str = Form(""),
    port_of_discharge: str = Form(""),
    etd: Optional[str] = Form(None),
    eta: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if db.query(models.Voyage).filter(models.Voyage.voyage_no == voyage_no).first():
        return JSONResponse({"error": f"航次編號 '{voyage_no}' 已存在"}, status_code=409)
    from datetime import date
    voyage = models.Voyage(
        voyage_no=voyage_no, ship_id=ship_id,
        port_of_loading=port_of_loading, port_of_discharge=port_of_discharge,
        etd=date.fromisoformat(etd) if etd else None,
        eta=date.fromisoformat(eta) if eta else None,
        status="計畫中",
    )
    db.add(voyage)
    db.commit()
    db.refresh(voyage)
    return JSONResponse(_voyage_json(voyage))


@router.post("/api/{voyage_id}")
def api_update_voyage(
    voyage_id: int,
    ship_id: int = Form(...),
    port_of_loading: str = Form(""),
    port_of_discharge: str = Form(""),
    etd: Optional[str] = Form(None),
    eta: Optional[str] = Form(None),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    voyage = db.query(models.Voyage).filter(models.Voyage.id == voyage_id).first()
    if not voyage:
        return JSONResponse({"error": "航次不存在"}, status_code=404)
    from datetime import date
    voyage.ship_id = ship_id
    voyage.port_of_loading = port_of_loading
    voyage.port_of_discharge = port_of_discharge
    voyage.etd = date.fromisoformat(etd) if etd else None
    voyage.eta = date.fromisoformat(eta) if eta else None
    voyage.status = status
    db.commit()
    return JSONResponse(_voyage_json(voyage))


@router.post("/api/{voyage_id}/delete")
def api_delete_voyage(voyage_id: int, db: Session = Depends(get_db)):
    voyage = db.query(models.Voyage).filter(models.Voyage.id == voyage_id).first()
    if not voyage:
        return JSONResponse({"error": "航次不存在"}, status_code=404)
    if db.query(models.Invoice).filter(models.Invoice.voyage_id == voyage_id).count() > 0:
        return JSONResponse({"error": "航次已有關聯帳務，無法刪除"}, status_code=409)
    db.delete(voyage)
    db.commit()
    return JSONResponse({"ok": True})
