from datetime import date, datetime, timedelta
import os
from dotenv import load_dotenv
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
from database import SessionLocal
from utils.mailer import send_email

load_dotenv()

# 通知收件人 (若不需要可移至外層設定，此處保留供發信使用)
NOTIFICATION_RECIPIENT = os.getenv("NOTIFICATION_RECIPIENT")
def check_and_send_reminders():
    print(f"[{datetime.now()}] 開始執行逾期帳單檢查任務...")
    db = SessionLocal()
    try:
        # 逾期標準：7 天前
        seven_days_ago = date.today() - timedelta(days=7)
        # 重複提醒標準：2 天前
        three_days_ago = datetime.now() - timedelta(days=1)

        overdue_invoices = (
            db.query(models.Invoice)
            .filter(models.Invoice.status != "已收款")
            .filter(models.Invoice.invoice_date <= seven_days_ago)
            .filter(
                or_(
                    models.Invoice.is_reminded == 0,
                    models.Invoice.last_reminded_at <= three_days_ago
                )
            )
            .all()
        )

        if not overdue_invoices:
            print("目前無逾期需提醒之帳單。")
            return

        for inv in overdue_invoices:
            is_repeat = inv.is_reminded == 1
            type_str = "【重複催收】" if is_repeat else "【逾期提醒】"
            subject = f"{type_str} 帳單編號：{inv.invoice_no} 已逾 7 天未結清"
            html = f"""
            <html>
                <body>
                    <h2>帳務逾期提醒信</h2>
                    <p>您好，以下帳單已超過 7 天未完成結算，請儘速處理：</p>
                    <table border="1" cellpadding="5" style="border-collapse: collapse;">
                        <tr style="background-color: #f2f2f2;">
                            <th>帳單編號</th>
                            <th>客戶名稱</th>
                            <th>帳單日期</th>
                            <th>負責人</th>
                            <th>金額</th>
                            <th>目前狀態</th>
                        </tr>
                        <tr>
                            <td>{inv.invoice_no}</td>
                            <td>{inv.customer_name}</td>
                            <td>{inv.invoice_date}</td>
                            <td>{inv.responsible}</td>
                            <td style="color: red;">{inv.total_amount:,.2f}</td>
                            <td>{inv.status}</td>
                        </tr>
                    </table>
                    <p>請登入系統進行確認：<a href="http://10.2.4.15:8000/invoices/{inv.id}">點此查看帳單詳情</a></p>
                    <br>
                    <p>系統自動發送，請勿直接回覆。</p>
                </body>
            </html>
            """
            
            # 發送給預設收件人
            success = send_email(subject, html, NOTIFICATION_RECIPIENT)
            if success:
                inv.is_reminded = 1
                inv.last_reminded_at = datetime.now()
                print(f"已成功寄送提醒信：{inv.invoice_no}")
            
        db.commit()
    except Exception as e:
        print(f"檢查任務發生錯誤: {e}")
        db.rollback()
    finally:
        db.close()
