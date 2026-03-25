#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 contact.csv 讀取 email 通訊錄，寄出 USDT/TWD 最新價

使用 emailData/appsettings.json 中的 EmailSettings 設定
contact.csv 格式：
name, line_id, line_token,email
miahcael,'Uxxxx','token...','mail'
"""

import csv
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from typing import List, Dict, Optional

from max_usdt_twd_fetcher import get_usdt_twd_ticker
import requests

CONTACT_FILE = 'contact.csv'
APPSETTINGS_FILE = 'emailData/appsettings.json'
MAX_API_BASE = 'https://max-api.maicoin.com/api/v2/tickers'


def get_crypto_prices() -> Optional[Dict[str, float]]:
    """取得 BTC/USDT, ETH/USDT, USDT/TWD 的最新價格"""
    prices = {}
    
    # 取得 BTC/USDT
    try:
        resp = requests.get(f"{MAX_API_BASE}/btcusdt", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            ticker = data.get('ticker', data)
            prices['BTC/USDT'] = float(ticker.get('last', 0))
    except Exception as e:
        print(f"⚠️ 無法取得 BTC/USDT: {e}")
    
    # 取得 ETH/USDT
    try:
        resp = requests.get(f"{MAX_API_BASE}/ethusdt", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            ticker = data.get('ticker', data)
            prices['ETH/USDT'] = float(ticker.get('last', 0))
    except Exception as e:
        print(f"⚠️ 無法取得 ETH/USDT: {e}")
    
    # 取得 USDT/TWD
    try:
        resp = requests.get(f"{MAX_API_BASE}/usdttwd", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            ticker = data.get('ticker', data)
            prices['USDT/TWD'] = float(ticker.get('last', 0))
    except Exception as e:
        print(f"⚠️ 無法取得 USDT/TWD: {e}")
    
    return prices if prices else None


def load_email_settings() -> Optional[Dict]:
    """讀取 appsettings.json 中的 EmailSettings"""
    try:
        with open(APPSETTINGS_FILE, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
        return config.get('EmailSettings')
    except Exception as e:
        print(f"❌ 讀取 appsettings.json 失敗: {e}")
        return None


def load_contacts() -> List[Dict[str, str]]:
    """讀取 contact.csv，回傳含 email 的聯絡人列表"""
    contacts: List[Dict[str, str]] = []

    with open(CONTACT_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = (row.get('email') or '').strip().strip("'\"")
            if not email:
                continue

            contact = {
                'name': (row.get('name') or '').strip().strip("'\""),
                'email': email,
            }
            contacts.append(contact)

    return contacts


def send_email(to_email: str, body: str, settings: Dict, usdt_twd_price: str = '', name: str = '') -> bool:
    """寄送純文字 Email"""
    try:
        smtp_host = settings.get('SmtpServer')
        smtp_port = settings.get('SmtpPort', 587)
        use_ssl = settings.get('UseSsl', True)
        sender_email = settings.get('SenderEmail')
        sender_password = settings.get('SenderPassword')
        sender_name = settings.get('SenderName', 'Rate Bot')
        email_subject = settings.get('EmailSubject', 'USDT/TWD 最新價')

        # 如果有 USDT/TWD 價格，加到標題最前面
        if usdt_twd_price:
            email_subject = f"{usdt_twd_price} {email_subject}"

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(email_subject, 'utf-8')
        # 正確設定 From 標題，只用寄件者名稱
        msg['From'] = Header(sender_name, 'utf-8').encode()
        msg['To'] = to_email

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if use_ssl:
                server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"❌ 寄給 {name or to_email} 失敗：{e}")
        return False


def main() -> None:
    # 先讀取 appsettings.json
    print('🔄 正在讀取 emailData/appsettings.json...')
    settings = load_email_settings()
    if not settings:
        print('❌ 無法讀取 email 設定')
        return

    print('✅ 已讀取 email 設定')

    # 讀取聯絡人
    print('🔄 正在讀取 contact.csv...')
    contacts = load_contacts()

    if not contacts:
        print('⚠️ contact.csv 中沒有 email 資料')
        return

    print(f"✅ 讀取到 {len(contacts)} 筆 email 聯絡人")

    # 取得加密貨幣價格
    print('🔄 正在取得 BTC/USDT, ETH/USDT, USDT/TWD 最新價...')
    prices = get_crypto_prices()
    if not prices:
        print('❌ 無法取得行情資料')
        return

    # 組織信件內容
    body_lines = []
    usdt_twd_price = ''
    
    for pair, price in prices.items():
        body_lines.append(f"{pair}: {price}")
        # 提取 USDT/TWD 價格用於標題
        if pair == 'USDT/TWD':
            usdt_twd_price = str(price)
    
    body = '\n'.join(body_lines)
    print(f"📈 本次要寄出的價格:\n{body}")

    for c in contacts:
        name = c['name'] or '(no-name)'
        email = c['email']
        print(f"\n📧 寄給 {name} <{email}> ...")
        ok = send_email(email, body, settings, usdt_twd_price=usdt_twd_price, name=name)
        if ok:
            print('   ✅ 寄信成功')
        else:
            print('   ❌ 寄信失敗')


if __name__ == '__main__':
    main()
