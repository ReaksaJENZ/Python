import requests
from flask import current_app

def send_telegram_message(message):
    BOT_TOKEN = current_app.config.get('BOT_TOKEN')
    CHAT_ID = current_app.config.get('CHAT_ID')
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram send error:", e)
