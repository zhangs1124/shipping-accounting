import sys
import os

# 加入專案路徑以匯入 models
sys.path.append(r"d:\project\Voyage\shipping-accounting")

import models
from database import SessionLocal

def test_uniqueness():
    db = SessionLocal()
    try:
        # 先清空測試用的資料 (或是找兩艘存在的船)
        ship1 = db.query(models.Ship).first()
        ship2 = db.query(models.Ship).offset(1).first()
        
        if not ship1 or not ship2:
            print("需要至少兩艘船來測試。")
            return

        v_no = "TEST-UNIQUE-999"
        
        print(f"嘗試建立船 1 ({ship1.name}) 的航次 {v_no}...")
        v1 = models.Voyage(voyage_no=v_no, ship_id=ship1.id, status="計畫中")
        db.add(v1)
        db.commit()
        print("成功建立第一筆。")

        print(f"嘗試建立船 2 ({ship2.name}) 的相同航次 {v_no}...")
        v2 = models.Voyage(voyage_no=v_no, ship_id=ship2.id, status="計畫中")
        db.add(v2)
        db.commit()
        print("成功建立第二筆「不同船、同編號」！ (這代表複合唯一限制生效)")

        print(f"嘗試再次建立船 1 的相同航次 {v_no} (預期失敗)...")
        v3 = models.Voyage(voyage_no=v_no, ship_id=ship1.id, status="計畫中")
        db.add(v3)
        try:
            db.commit()
            print("錯誤：竟然成功建立了「同船、同編號」！")
        except Exception as e:
            db.rollback()
            print(f"正確攔截錯誤：{e}")

        # 清理測試資料
        db.delete(v1)
        db.delete(v2)
        db.commit()
        print("測試資料清理完畢。")

    finally:
        db.close()

if __name__ == "__main__":
    # 設定環境變數為開發環境，確保連接到 shipping_dev.db
    os.environ["APP_ENV"] = "development"
    test_uniqueness()
