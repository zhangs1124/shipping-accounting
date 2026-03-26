import sys
from database import SessionLocal
import models
from utils.audit_logger import set_audit_context

db = SessionLocal()

# Mock web context
set_audit_context(user_id=1, ip_address="test_ip")

try:
    # 1. Test Create
    dept = models.Department(name="TestDept_AuditLogs_123", description="test")
    db.add(dept)
    db.commit()
    print("Created dept, id:", dept.id)

    # 2. Test Update
    dept.description = "updated"
    db.commit()
    print("Updated dept")

    # 3. Test Delete
    db.delete(dept)
    db.commit()
    print("Deleted dept")

except Exception as e:
    print("Error during DB operations:", repr(e))
    db.rollback()

print("--- AUDIT LOGS ---")
logs = db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).limit(10).all()
for l in logs:
    print(f"[{l.id}] {l.action} on {l.table_name} (ID: {l.target_id}) - IP: {l.ip_address} - User: {l.user_id}")
    print(f"  Old: {l.old_value}")
    print(f"  New: {l.new_value}")
