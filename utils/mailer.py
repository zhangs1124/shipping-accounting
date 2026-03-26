import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os
from dotenv import load_dotenv

load_dotenv()

# SMTP 設定
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")

def send_email(subject: str, html_content: str, recipient: str) -> bool:
    """
    純粹負責建立 SMTP 連線並寄送 Email 的共用工具函式。
    
    :param subject: 信件主旨
    :param html_content: HTML 格式的信件內容
    :param recipient: 收件人 Email 地址
    :return: 寄送成功回傳 True，否則回傳 False
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("SMTP 設定不完整，跳過寄信。")
        return False

    msg = MIMEMultipart()
    # 參考範本，設定顯示名稱與標頭編碼
    msg['From'] = f"{Header('船務部帳務系統', 'utf-8').encode()} <{MAIL_FROM}>"
    msg['To'] = recipient
    msg['Subject'] = Header(subject, 'utf-8')

    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"郵件發送失敗: {e}")
        return False
