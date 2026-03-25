from database import SessionLocal
import models
from datetime import date, timedelta
from tasks.email_tasks import check_and_send_reminders

db = SessionLocal()
try:
    # 找尋現有的航次
    v = db.query(models.Voyage).first()
    if not v:
        print("資料庫無航次，無法測試。正在建立一個預設航次...")
        # 需先有船
        s = db.query(models.Ship).first()
        if not s:
            s = models.Ship(code="TEST-SHIP", name="測試船")
            db.add(s)
            db.flush()
        v = models.Voyage(voyage_no="T001", ship_id=s.id, status="進行中")
        db.add(v)
        db.flush()
    
    # 建立一筆測試用的逾期帳單 (10天前)
    test_inv = models.Invoice(
        invoice_no=f"TS-{int(date.today().strftime('%m%d%H%M'))}",
        voyage_id=v.id,
        customer_name="張小姐 (測試)",
        invoice_date=date.today() - timedelta(days=10),
        status="草稿",
        responsible="Antigravity",
        total_amount=999.00,
        is_reminded=0
    )
    db.add(test_inv)
    db.commit()
    print(f"✅ 測試用逾期帳單已建立: {test_inv.invoice_no}")

    # 立即執行提醒檢查
    print("🚀 正在執行 check_and_send_reminders()...")
    check_and_send_reminders()
    print("🏁 檢查執行完畢，請確認控制台輸出。")

finally:
    db.close()
