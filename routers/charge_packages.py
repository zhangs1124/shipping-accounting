from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from utils.templates import templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models
from database import get_db

router = APIRouter(prefix="/charge-packages", tags=["charge_packages"])

@router.get("", response_class=HTMLResponse)
def list_packages(request: Request, db: Session = Depends(get_db)):
    packages = db.query(models.ChargePackage).order_by(models.ChargePackage.name).all()
    return templates.TemplateResponse("charge_packages/list.html", {
        "request": request,
        "packages": packages
    })


@router.post("")
def create_package(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    pkg = models.ChargePackage(name=name.strip(), description=description.strip())
    db.add(pkg)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(url="/charge-packages?error=組套名稱已存在", status_code=303)
    
    return RedirectResponse(url="/charge-packages", status_code=303)


@router.get("/{package_id}/edit", response_class=HTMLResponse)
def edit_package(package_id: int, request: Request, db: Session = Depends(get_db)):
    pkg = db.query(models.ChargePackage).filter(models.ChargePackage.id == package_id).first()
    if not pkg:
        return RedirectResponse(url="/charge-packages", status_code=303)
        
    charge_items = db.query(models.ChargeItem).order_by(models.ChargeItem.code).all()
    
    # 找出尚未加入此組套的收費項目
    existing_item_ids = [item.charge_item_id for item in pkg.items]
    available_items = [ci for ci in charge_items if ci.id not in existing_item_ids]
    
    return templates.TemplateResponse("charge_packages/edit.html", {
        "request": request,
        "package": pkg,
        "available_items": available_items
    })


@router.post("/{package_id}/edit")
def update_package(
    package_id: int,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    pkg = db.query(models.ChargePackage).filter(models.ChargePackage.id == package_id).first()
    if not pkg:
        return RedirectResponse(url="/charge-packages", status_code=303)
        
    pkg.name = name.strip()
    pkg.description = description.strip()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(url=f"/charge-packages/{package_id}/edit?error=組套名稱已存在", status_code=303)
        
    return RedirectResponse(url="/charge-packages", status_code=303)


@router.post("/{package_id}/delete")
def delete_package(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(models.ChargePackage).filter(models.ChargePackage.id == package_id).first()
    if pkg:
        db.delete(pkg)
        db.commit()
    return RedirectResponse(url="/charge-packages", status_code=303)


@router.post("/{package_id}/items")
def add_package_item(
    package_id: int,
    charge_item_id: int = Form(...),
    default_quantity: float = Form(1.0),
    db: Session = Depends(get_db)
):
    pkg = db.query(models.ChargePackage).filter(models.ChargePackage.id == package_id).first()
    if not pkg:
        return RedirectResponse(url="/charge-packages", status_code=303)
        
    # Check if already exists
    existing = db.query(models.ChargePackageItem).filter(
        models.ChargePackageItem.package_id == package_id,
        models.ChargePackageItem.charge_item_id == charge_item_id
    ).first()
    
    if existing:
        return RedirectResponse(url=f"/charge-packages/{package_id}/edit?error=該費用已在組套中", status_code=303)
        
    new_item = models.ChargePackageItem(
        package_id=package_id,
        charge_item_id=charge_item_id,
        default_quantity=default_quantity
    )
    db.add(new_item)
    db.commit()
    
    return RedirectResponse(url=f"/charge-packages/{package_id}/edit", status_code=303)


@router.post("/{package_id}/items/{item_id}/delete")
def delete_package_item(package_id: int, item_id: int, db: Session = Depends(get_db)):
    pkg_item = db.query(models.ChargePackageItem).filter(
        models.ChargePackageItem.id == item_id,
        models.ChargePackageItem.package_id == package_id
    ).first()
    
    if pkg_item:
        db.delete(pkg_item)
        db.commit()
        
    return RedirectResponse(url=f"/charge-packages/{package_id}/edit", status_code=303)
