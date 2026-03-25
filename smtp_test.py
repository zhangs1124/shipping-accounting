import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
NOTIFICATION_RECIPIENT = os.getenv("NOTIFICATION_RECIPIENT")

def test_send():
    print(f"嘗試從 {MAIL_FROM} 寄信給 {NOTIFICATION_RECIPIENT}...")
    msg = MIMEMultipart()
    msg['From'] = f"{Header('船務部帳務系統測試', 'utf-8').encode()} <{MAIL_FROM}>"
    msg['To'] = NOTIFICATION_RECIPIENT
    msg['Subject'] = Header("系統整合測試信 (無資料庫版本)", "utf-8")
    
    body = "這是一封來自船務部帳務系統的測試信件，旨在驗證 SMTP 設定是否正確。"
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ 郵件發送成功！")
        return True
    except Exception as e:
        print(f"❌ 郵件發送失敗: {e}")
        return False

if __name__ == "__main__":
    test_send()
