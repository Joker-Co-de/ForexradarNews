import os
import json
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
# ============================================================
# PIPPULSE — FOREX NEWS TELEGRAM BOT
# ============================================================
BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHANNEL_ID"]
# Forex Factory / Fair Economy weekly calendar JSON
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
# File used to remember alerts already sent
SENT_FILE = "sent_events.json"
# Nigeria time
NIGERIA_TZ = ZoneInfo("Africa/Lagos")
# ============================================================
# LOAD SENT EVENTS
# ============================================================
def load_sent_events():
    try:
        with open(SENT_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            return set(data)
        if isinstance(data, dict):
            return set(data.keys())
        return set()
    except (FileNotFoundError, json.JSONDecodeError):
        return set()
# ============================================================
# SAVE SENT EVENTS
# ============================================================
def save_sent_events(sent_events):
    with open(SENT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            sorted(sent_events),
            file,
            indent=2,
            ensure_ascii=False
        )
# ============================================================
# DOWNLOAD CALENDAR
# ============================================================
def get_calendar():
    headers = {
        "User-Agent": "PipPulse/1.0"
    }
    response = requests.get(
        CALENDAR_URL,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Unexpected calendar format.")
    return data
# ============================================================
# TELEGRAM
# ============================================================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=30
    )
    print(response.text)
    response.raise_for_status()
# ============================================================
# FORMAT EVENT
# ============================================================
def format_event(event):
    title = event.get("title", "Unknown Event")
    currency = event.get("country", "Unknown")
    impact = event.get("impact", "Unknown")
    date_string = event.get("date", "")
    forecast = event.get("forecast", "")
    previous = event.get("previous", "")
    # Convert event time to Nigeria time
    try:
        event_time = datetime.fromisoformat(
            date_string.replace("Z", "+00:00")
        )
        nigeria_time = event_time.astimezone(NIGERIA_TZ)
        formatted_time = nigeria_time.strftime(
            "%A, %d %B %Y • %I:%M %p WAT"
        )
    except Exception:
        formatted_time = date_string
    forecast_text = forecast if forecast else "N/A"
    previous_text = previous if previous else "N/A"
    message = (
        "🚨 PIPPULSE HIGH-IMPACT NEWS\n"
        "\n"
        f"🔴 Impact: {impact}\n"
        f"💱 Currency: {currency}\n"
        f"📰 Event: {title}\n"
        f"⏰ Time: {formatted_time}\n"
        "\n"
        f"📊 Forecast: {forecast_text}\n"
        f"📉 Previous: {previous_text}\n"
        "\n"
        "⚠️ High-impact news can cause sharp volatility.\n"
        "Manage your risk carefully.\n"
        "\n"
        "🔗 Forex Factory Calendar:\n"
        "https://www.forexfactory.com/calendar"
    )
    return message
# ============================================================
# MAIN
# ============================================================
def main():
    print("🚀 PipPulse starting...")
    sent_events = load_sent_events()
    print(f"Already recorded events: {len(sent_events)}")
    calendar = get_calendar()
    print(f"Calendar events received: {len(calendar)}")
    new_alerts = 0
    for event in calendar:
        # Only High-impact events
        if str(event.get("impact", "")).strip().lower() != "high":
            continue
        title = event.get("title", "").strip()
        currency = event.get("country", "").strip()
        date_string = event.get("date", "").strip()
        if not title or not date_string:
            continue
        # Unique identifier for the event
        event_id = f"{date_string}|{currency}|{title}"
        # Don't send the same event twice
        if event_id in sent_events:
            continue
        message = format_event(event)
        print(f"Sending alert: {currency} - {title}")
        send_telegram(message)
        sent_events.add(event_id)
        new_alerts += 1
    save_sent_events(sent_events)
    print(f"✅ Done. New alerts sent: {new_alerts}")
if __name__ == "__main__":
    main()
