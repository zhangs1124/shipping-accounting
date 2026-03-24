"""
範例資料產生腳本
執行方式：python seed_data.py
"""
from decimal import Decimal
from datetime import date
from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 清除舊資料（依外鍵順序）
db.query(models.InvoiceLine).delete()
db.query(models.Invoice).delete()
db.query(models.Voyage).delete()
db.query(models.Ship).delete()
db.query(models.ChargeItem).delete()
db.commit()

# ── 船舶 ──────────────────────────────────────────
ships = [
    models.Ship(code="EVER-GIVEN",   name="長賜號",   flag="巴拿馬",   ship_type="貨櫃船"),
    models.Ship(code="COSCO-STAR",   name="中遠之星", flag="中國",     ship_type="貨櫃船"),
    models.Ship(code="WAN-HAI-301",  name="萬海301",  flag="台灣",     ship_type="貨櫃船"),
    models.Ship(code="YANG-MING-01", name="陽明一號", flag="台灣",     ship_type="散裝船"),
]
db.add_all(ships)
db.commit()
for s in ships:
    db.refresh(s)

# ── 航次 ──────────────────────────────────────────
voyages = [
    models.Voyage(voyage_no="EG-2024-001", ship_id=ships[0].id,
                  port_of_loading="高雄", port_of_discharge="鹿特丹",
                  etd=date(2024, 3, 1), eta=date(2024, 4, 5), status="已完成"),
    models.Voyage(voyage_no="CS-2024-012", ship_id=ships[1].id,
                  port_of_loading="上海", port_of_discharge="高雄",
                  etd=date(2024, 6, 10), eta=date(2024, 6, 14), status="已完成"),
    models.Voyage(voyage_no="WH-2024-033", ship_id=ships[2].id,
                  port_of_loading="高雄", port_of_discharge="東京",
                  etd=date(2024, 9, 20), eta=date(2024, 9, 25), status="進行中"),
    models.Voyage(voyage_no="YM-2025-001", ship_id=ships[3].id,
                  port_of_loading="基隆", port_of_discharge="新加坡",
                  etd=date(2025, 1, 15), eta=date(2025, 1, 22), status="計畫中"),
]
db.add_all(voyages)
db.commit()
for v in voyages:
    db.refresh(v)

# ── 收費項目 ──────────────────────────────────────
charge_items = [
    models.ChargeItem(code="PORT-FEE",    name="港口費",     currency="TWD", default_unit_price=Decimal("15000")),
    models.ChargeItem(code="AGENT-FEE",   name="代理費",     currency="TWD", default_unit_price=Decimal("8000")),
    models.ChargeItem(code="THC",         name="貨櫃處理費", currency="USD", default_unit_price=Decimal("120")),
    models.ChargeItem(code="DOC-FEE",     name="文件費",     currency="TWD", default_unit_price=Decimal("1500")),
    models.ChargeItem(code="PILOTAGE",    name="引水費",     currency="TWD", default_unit_price=Decimal("25000")),
    models.ChargeItem(code="TOWAGE",      name="拖船費",     currency="TWD", default_unit_price=Decimal("18000")),
    models.ChargeItem(code="CUSTOMS-FEE", name="報關費",     currency="TWD", default_unit_price=Decimal("3500")),
    models.ChargeItem(code="STORAGE",     name="倉儲費",     currency="TWD", default_unit_price=Decimal("500")),
]
db.add_all(charge_items)
db.commit()
for ci in charge_items:
    db.refresh(ci)

# ── 帳務主項目 ────────────────────────────────────
invoices = [
    models.Invoice(invoice_no="INV-2024-001", voyage_id=voyages[0].id,
                   customer_name="台灣貨運股份有限公司",
                   invoice_date=date(2024, 4, 10), status="已收款", total_amount=Decimal("0")),
    models.Invoice(invoice_no="INV-2024-002", voyage_id=voyages[1].id,
                   customer_name="中華海運代理有限公司",
                   invoice_date=date(2024, 6, 20), status="已開立", total_amount=Decimal("0")),
    models.Invoice(invoice_no="INV-2024-003", voyage_id=voyages[2].id,
                   customer_name="萬海航運股份有限公司",
                   invoice_date=date(2024, 9, 28), status="草稿",   total_amount=Decimal("0")),
]
db.add_all(invoices)
db.commit()
for inv in invoices:
    db.refresh(inv)

# ── 帳務明細 ──────────────────────────────────────
def add_line(invoice, ci, qty, price=None, currency=None, remark=""):
    p = Decimal(str(price)) if price else ci.default_unit_price
    c = currency or ci.currency
    subtotal = Decimal(str(qty)) * p
    line = models.InvoiceLine(
        invoice_id=invoice.id,
        charge_item_id=ci.id,
        quantity=Decimal(str(qty)),
        unit_price=p,
        currency=c,
        subtotal=subtotal,
        remark=remark,
    )
    db.add(line)
    return subtotal

# INV-2024-001 明細
t = Decimal("0")
t += add_line(invoices[0], charge_items[0], 1)           # 港口費
t += add_line(invoices[0], charge_items[1], 1)           # 代理費
t += add_line(invoices[0], charge_items[2], 10, 120, "USD", "20呎櫃×10")  # THC
t += add_line(invoices[0], charge_items[3], 1)           # 文件費
t += add_line(invoices[0], charge_items[4], 1)           # 引水費
t += add_line(invoices[0], charge_items[5], 2)           # 拖船費×2
invoices[0].total_amount = t

# INV-2024-002 明細
t = Decimal("0")
t += add_line(invoices[1], charge_items[0], 1)           # 港口費
t += add_line(invoices[1], charge_items[1], 1)           # 代理費
t += add_line(invoices[1], charge_items[6], 1)           # 報關費
t += add_line(invoices[1], charge_items[3], 2, 1500, "TWD", "進出口各一份")
invoices[1].total_amount = t

# INV-2024-003 明細（草稿，可繼續編輯）
t = Decimal("0")
t += add_line(invoices[2], charge_items[0], 1)           # 港口費
t += add_line(invoices[2], charge_items[4], 1)           # 引水費
t += add_line(invoices[2], charge_items[7], 5, 500, "TWD", "5天倉儲")
invoices[2].total_amount = t

db.commit()
db.close()

print("✅ 範例資料建立完成！")
print(f"   船舶：{len(ships)} 筆")
print(f"   航次：{len(voyages)} 筆")
print(f"   收費項目：{len(charge_items)} 筆")
print(f"   帳務主項目：{len(invoices)} 筆（含明細）")
