from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models
from database import SessionLocal

def generate_task_reminders():
    """
    掃描所有進行中的航次，針對尚未完成的進出港任務產生提醒。
    """
    print(f"[{datetime.now()}] 開始掃描背景提醒任務...")
    db = SessionLocal()
    try:
        # 1. 取得所有進行中的航次
        active_voyages = db.query(models.Voyage).filter(
            models.Voyage.status == "進行中"
        ).all()
        
        for voyage in active_voyages:
            # 取得該航次的負責人員 (operator)
            operator_id = voyage.operator_id
            if not operator_id:
                continue # 若未指定負責人則跳過自動提醒
                
            # 2. 取得該航次所有尚未完成的任務紀錄
            pending_logs = db.query(models.VoyageTaskLog).filter(
                models.VoyageTaskLog.voyage_id == voyage.id,
                models.VoyageTaskLog.recorded_time == None
            ).all()
            
            for log in pending_logs:
                # 檢查任務類別是否有設定基準點與偏移
                category = log.task_category
                if not category or not category.base_milestone:
                    continue
                    
                # 計算預計期限 (Deadline)
                base_time = None
                if category.base_milestone == "ETA":
                    base_time = voyage.eta
                elif category.base_milestone == "ETD":
                    base_time = voyage.etd
                
                if not base_time:
                    continue
                
                # 將 date 轉換為 datetime (以便計算)
                if isinstance(base_time, datetime):
                    dt_base = base_time
                else:
                    dt_base = datetime.combine(base_time, datetime.min.time())
                
                deadline = dt_base + timedelta(hours=category.expected_offset_hours or 0)
                
                # 3. 判斷是否已逾期 (現在時間已過 Deadline)
                if datetime.now() >= deadline:
                    # 檢查提醒表中是否已存在該項目的未結案提醒
                    existing = db.query(models.Reminder).filter(
                        models.Reminder.source_table == "voyage_task_logs",
                        models.Reminder.source_id == log.id,
                        models.Reminder.is_closed == 0
                    ).first()
                    
                    if not existing:
                        # 建立新提醒
                        new_reminder = models.Reminder(
                            title=f"任務逾期：{voyage.voyage_no} - {category.name}",
                            content=f"航次 {voyage.voyage_no} ({voyage.ship.name}) 的「{category.name}」項目已超過預計時間 ({deadline.strftime('%m/%d %H:%M')})，請儘速處理。",
                            remind_type="TASK_OVERDUE",
                            source_table="voyage_task_logs",
                            source_id=log.id,
                            target_employee_id=operator_id,
                            deadline=deadline
                        )
                        db.add(new_reminder)
                        print(f"產生提醒：{new_reminder.title} -> 給人員 ID {operator_id}")
        
        db.commit()
    except Exception as e:
        print(f"背景掃描發生錯誤: {e}")
        db.rollback()
    finally:
        db.close()
