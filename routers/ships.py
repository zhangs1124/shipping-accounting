from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from database import get_db

router = APIRouter(prefix="/ships", tags=["ships"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
def list_ships(request: Request, db: Session = Depends(get_db)):
    ships = db.query(models.Ship).order_by(models.Ship.code).all()
    return templates.TemplateResponse("ships/list.html", {"request": request, "ships": ships})


# ── JSON API（供 Modal 使用）──────────────────────

@router.post("/api")
def api_create_ship(
    code: str = Form(...), name: str = Form(...),
    flag: str = Form(""), ship_type: str = Form(""),
    db: Session = Depends(get_db),
):
    if db.query(models.Ship).filter(models.Ship.code == code).first():
        return JSONResponse({"error": f"船舶代碼 '{code}' 已存在"}, status_code=409)
    ship = models.Ship(code=code, name=name, flag=flag, ship_type=ship_type)
    db.add(ship)
    db.commit()
    db.refresh(ship)
    return JSONResponse({"id": ship.id, "code": ship.code, "name": ship.name,
                         "flag": ship.flag or "", "ship_type": ship.ship_type or ""})


@router.post("/api/{ship_id}")
def api_update_ship(
    ship_id: int, name: str = Form(...),
    flag: str = Form(""), ship_type: str = Form(""),
    db: Session = Depends(get_db),
):
    ship = db.query(models.Ship).filter(models.Ship.id == ship_id).first()
    if not ship:
        return JSONResponse({"error": "船舶不存在"}, status_code=404)
    ship.name = name; ship.flag = flag; ship.ship_type = ship_type
    db.commit()
    return JSONResponse({"id": ship.id, "code": ship.code, "name": ship.name,
                         "flag": ship.flag or "", "ship_type": ship.ship_type or ""})


@router.post("/api/{ship_id}/delete")
def api_delete_ship(ship_id: int, db: Session = Depends(get_db)):
    ship = db.query(models.Ship).filter(models.Ship.id == ship_id).first()
    if not ship:
        return JSONResponse({"error": "船舶不存在"}, status_code=404)
    if db.query(models.Voyage).filter(models.Voyage.ship_id == ship_id).count() > 0:
        return JSONResponse({"error": "船舶已有關聯航次，無法刪除"}, status_code=409)
    db.delete(ship)
    db.commit()
    return JSONResponse({"ok": True})
