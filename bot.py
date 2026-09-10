import os
import json
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
# ============================================================
# PIPPULSE — FOREX NEWS RADAR
# 15-MINUTE WARNING + RELEASE ALERT
# ============================================================
BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHANNEL_ID"]
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
SENT_FILE = "sent_events.json"
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
# GET FOREX FACTORY CALENDAR
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
# SEND TELEGRAM MESSAGE
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
# PARSE EVENT TIME
# ============================================================
def parse_event_time(date_string):
    """
    Convert Forex Factory event time to UTC.
    Forex Factory's JSON dates are normally ISO timestamps.
    """
    event_time = datetime.fromisoformat(
        date_string.replace("Z", "+00:00")
    )
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
    return event_time.astimezone(timezone.utc)
# ============================================================
# FORMAT TIME FOR NIGERIA
# ============================================================
def nigeria_time(event_time):
    return event_time.astimezone(NIGERIA_TZ).strftime(
        "%A, %d %B %Y • %I:%M %p WAT"
    )
# ============================================================
# FORMAT WARNING MESSAGE
# ============================================================
def warning_message(event, event_time):
    title = event.get("title", "Unknown Event")
    currency = event.get("country", "Unknown")
    forecast = event.get("forecast", "")
    previous = event.get("previous", "")
    forecast_text = forecast if forecast else "N/A"
    previous_text = previous if previous else "N/A"
    return (
        "⏰ PIPPULSE — 15 MINUTE WARNING\n"
        "\n"
        f"🔴 High Impact\n"
        f"💱 Currency: {currency}\n"
        f"📰 Event: {title}\n"
        f"⏱️ Release: {nigeria_time(event_time)}\n"
        "\n"
        f"📊 Forecast: {forecast_text}\n"
        f"📉 Previous: {previous_text}\n"
        "\n"
        "⚠️ HIGH VOLATILITY EXPECTED\n"
        "Consider reducing risk and avoid entering blindly before the release.\n"
        "\n"
        "🔗 Forex Factory Calendar:\n"
        "https://www.forexfactory.com/calendar"
    )
# ============================================================
# FORMAT RELEASE MESSAGE
# ============================================================
def release_message(event, event_time):
    title = event.get("title", "Unknown Event")
    currency = event.get("country", "Unknown")
    forecast = event.get("forecast", "")
    previous = event.get("previous", "")
    actual = event.get("actual", "")
    forecast_text = forecast if forecast else "N/A"
    previous_text = previous if previous else "N/A"
    actual_text = actual if actual else "Waiting for actual"
    return (
        "🚨 PIPPULSE — NEWS RELEASED\n"
        "\n"
        f"🔴 HIGH IMPACT\n"
        f"💱 Currency: {currency}\n"
        f"📰 Event: {title}\n"
        f"⏰ Release: {nigeria_time(event_time)}\n"
        "\n"
        f"📌 Actual: {actual_text}\n"
        f"📊 Forecast: {forecast_text}\n"
        f"📉 Previous: {previous_text}\n"
        "\n"
        "⚠️ Market volatility may increase sharply.\n"
        "Trade with proper risk management.\n"
        "\n"
        "🔗 Forex Factory Calendar:\n"
        "https://www.forexfactory.com/calendar"
    )
# ============================================================
# MAIN
# ============================================================
def main():
    print("🚀 PipPulse starting...")
    sent_events = load_sent_events()
    print(f"Recorded alerts: {len(sent_events)}")
    calendar = get_calendar()
    print(f"Calendar events received: {len(calendar)}")
    # Current UTC time
    now = datetime.now(timezone.utc)
    new_alerts = 0
    for event in calendar:
        # ----------------------------------------------------
        # ONLY HIGH IMPACT
        # ----------------------------------------------------
        if str(event.get("impact", "")).strip().lower() != "high":
            continue
        title = event.get("title", "").strip()
        currency = event.get("country", "").strip()
        date_string = event.get("date", "").strip()
        if not title or not date_string:
            continue
        # ----------------------------------------------------
        # EVENT TIME
        # ----------------------------------------------------
        try:
            event_time = parse_event_time(date_string)
        except Exception as error:
            print(f"Could not parse event time: {error}")
            continue
        # ----------------------------------------------------
        # UNIQUE EVENT ID
        # ----------------------------------------------------
        event_id = f"{date_string}|{currency}|{title}"
        warning_id = event_id + "|15MIN"
        release_id = event_id + "|RELEASE"
        # ----------------------------------------------------
        # TIME UNTIL NEWS
        # ----------------------------------------------------
        seconds_until = (event_time - now).total_seconds()
        minutes_until = seconds_until / 60
        print(
            f"{currency} | {title} | "
            f"{minutes_until:.1f} minutes remaining"
        )
        # ====================================================
        # 15-MINUTE WARNING
        # ====================================================
        # Because GitHub runs every 5 minutes, we use a
        # window around the 15-minute mark.
        if 10 <= minutes_until <= 17:
            if warning_id not in sent_events:
                print(f"⏰ Sending 15-minute warning: {title}")
                send_telegram(
                    warning_message(event, event_time)
                )
                sent_events.add(warning_id)
                new_alerts += 1
        # ====================================================
        # RELEASE ALERT
        # ====================================================
        # GitHub runs every 5 minutes, so we allow a window
        # around the release time.
        elif -3 <= minutes_until <= 3:
            if release_id not in sent_events:
                print(f"🚨 Sending release alert: {title}")
                send_telegram(
                    release_message(event, event_time)
                )
                sent_events.add(release_id)
                new_alerts += 1
    # ========================================================
    # SAVE ALERT HISTORY
    # ========================================================
    save_sent_events(sent_events)
    print(
        f"✅ PipPulse finished. "
        f"New alerts sent: {new_alerts}"
    )
# ============================================================
# START
# ============================================================
if __name__ == "__main__":
    main()
