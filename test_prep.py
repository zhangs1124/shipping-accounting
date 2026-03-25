from database import SessionLocal
import models
from datetime import date, timedelta

db = SessionLocal()
try:
    # 檢查是否有逾期帳單
    seven_days_ago = date.today() - timedelta(days=7)
    overdue = db.query(models.Invoice).filter(models.Invoice.invoice_date <= seven_days_ago).all()
    
    print(f"目前逾期帳單數量: {len(overdue)}")
    for inv in overdue:
        print(f"ID: {inv.id}, 編號: {inv.invoice_no}, 日期: {inv.invoice_date}, 狀態: {inv.status}, 已提醒: {inv.is_reminded}")

    if not overdue:
        print("建立一筆測試用的逾期帳單...")
        # 建立一筆 15 天前的新帳單
        test_inv = models.Invoice(
            invoice_no="TEST-OVERDUE-001",
            voyage_id=1, # 假設 ID 1 存在
            customer_name="測試客戶",
            invoice_date=date.today() - timedelta(days=15),
            status="草稿",
            responsible="Antigravity Test",
            total_amount=1234.56,
            is_reminded=0
        )
        db.add(test_inv)
        db.commit()
        print("測試帳單已建立。")
    
finally:
    db.close()
