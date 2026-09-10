import os
import requests
BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHANNEL_ID"]
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": "🚨 PipPulse Telegram Test\n\n✅ Telegram connection is working!"
    }
)
print(response.text)
response.raise_for_status()
