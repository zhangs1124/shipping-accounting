from database import SessionLocal
import models
from datetime import date, timedelta
from sqlalchemy import text
from tasks.email_tasks import check_and_send_reminders

def debug_db():
    db = SessionLocal()
    try:
        # 1. 確保有航次，沒有就建立
        v = db.query(models.Voyage).first()
        if not v:
            # 確保有船
            s = db.query(models.Ship).first()
            if not s:
                s = models.Ship(code="S01", name="預設測試船")
                db.add(s)
                db.flush()
            v = models.Voyage(voyage_no="V01", ship_id=s.id)
            db.add(v)
            db.flush()
        
        # 2. 建立強制逾期帳單 (不管有沒有其他衝突，用個隨機編號)
        import random
        inv_no = f"TEST-{random.randint(1000, 9999)}"
        test_inv = models.Invoice(
            invoice_no=inv_no,
            voyage_id=v.id,
            customer_name="張小姐 (系統自動測試)",
            invoice_date=date.today() - timedelta(days=10),
            status="草稿",
            responsible="系統管理員",
            total_amount=500.0,
            is_reminded=0
        )
        db.add(test_inv)
        db.commit()
        print(f"✅ 成功建立測試帳單：{inv_no}")
        
        # 3. 執行提醒任務
        check_and_send_reminders()
        print("✅ 提醒任務執行完畢。")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    debug_db()
