from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
import models
from utils.auth import get_current_user
from utils.templates import templates

router = APIRouter(prefix="/audit-logs", tags=["audit_logs"])

@router.get("/")
def view_audit_logs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user)
):
    # 此處可以加上權限控管，例如必須是 Admin 角色
    # if current_user.role.name != "Admin":
    #     raise HTTPException(status_code=403, detail="無存取權限")
        
    logs = db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).all()
    
    # 為了讓前端方便顯示使用者名稱，這裡我們建立一個 user dict
    users = db.query(models.Employee).all()
    user_map = {u.id: u.full_name for u in users}
    user_map[None] = "系統"
    
    return templates.TemplateResponse(
        "audit_logs/list.html",
        {
            "request": request,
            "logs": logs,
            "user_map": user_map,
            "current_user": current_user
        }
    )
