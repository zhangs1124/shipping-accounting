from datetime import date, datetime
import models
from database import SessionLocal

def test_logic():
    db = SessionLocal()
    voyage = db.query(models.Voyage).first()
    if not voyage:
        print("No voyage found")
        return
    
    eta = "2026-04-20T11:20"
    arrival_date = "2026-04-20T11:55"
    etd = "2026-04-20"
    
    try:
        voyage.etd = date.fromisoformat(etd) if etd else None
        voyage.eta = datetime.fromisoformat(eta.replace(' ', 'T')) if eta else None
        voyage.arrival_date = datetime.fromisoformat(arrival_date.replace(' ', 'T')) if arrival_date else None
        db.commit()
        print("Success")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_logic()
