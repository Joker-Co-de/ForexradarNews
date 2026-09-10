import json
import os
import hashlib
import urllib.request
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

CALENDAR_URL = (
    "https://nfs.faireconomy.media/"
    "ff_calendar_thisweek.json"
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

WAT = ZoneInfo("Africa/Lagos")

CURRENCIES = {
    "USD", "EUR", "GBP", "JPY",
    "CAD", "AUD", "NZD", "CHF"
}

STATE_FILE = "sent_events.json"


def get_calendar():
    request = urllib.request.Request(
        CALENDAR_URL,
        headers={"User-Agent": "PipPulse/1.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def load_state():
    if not os.path.exists(STATE_FILE):
        return set()

    try:
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(state), f)


def send_telegram(message):
    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": CHANNEL_ID,
        "text": message
    }

    encoded = json.dumps(data).encode()

    request = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def event_id(event, alert_type):
    raw = (
        f"{event.get('date')}|"
        f"{event.get('country')}|"
        f"{event.get('title')}|"
        f"{alert_type}"
    )

    return hashlib.sha256(raw.encode()).hexdigest()


def format_event(event, alert_type):
    event_time = datetime.fromisoformat(
        event["date"]
    )

    wat_time = event_time.astimezone(WAT)

    currency = event.get("country", "")
    title = event.get("title", "")

    forecast = event.get("forecast", "")
    previous = event.get("previous", "")

    if alert_type == "warning":
        message = (
            "🔴 HIGH IMPACT NEWS — 30 MINUTES\n\n"
            f"🌍 {currency} — {title}\n"
            f"⏰ {wat_time.strftime('%I:%M %p')} WAT\n\n"
            f"📊 Forecast: {forecast or 'N/A'}\n"
            f"📉 Previous: {previous or 'N/A'}\n\n"
            "⚠️ Potential market volatility"
        )

    else:
        message = (
            "🚨 HIGH IMPACT NEWS — RELEASED\n\n"
            f"🌍 {currency} — {title}\n"
            f"⏰ {wat_time.strftime('%I:%M %p')} WAT\n\n"
            f"📊 Forecast: {forecast or 'N/A'}\n"
            f"📉 Previous: {previous or 'N/A'}\n\n"
            "⚡ Watch for increased volatility."
        )

    return message


def main():
    events = get_calendar()
    sent = load_state()

    now = datetime.now(timezone.utc)

    for event in events:

        if event.get("impact") != "High":
            continue

        if event.get("country") not in CURRENCIES:
            continue

        try:
            event_time = datetime.fromisoformat(
                event["date"]
            )
        except Exception:
            continue

        difference = event_time - now
        minutes = difference.total_seconds() / 60

        # 30-minute warning
        if 27 <= minutes <= 33:

            key = event_id(event, "warning")

            if key not in sent:
                send_telegram(
                    format_event(event, "warning")
                )
                sent.add(key)

        # Release alert
        elif -2 <= minutes <= 2:

            key = event_id(event, "release")

            if key not in sent:
                send_telegram(
                    format_event(event, "release")
                )
                sent.add(key)

    save_state(sent)


if __name__ == "__main__":
    main()
