import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger("telegram_service")

def get_bot_token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN") or "8934911720:AAFLoZmQuAyq75bNoWpYdkqT89q0JzVOfa8"

def get_default_chat_id() -> str:
    return os.getenv("TELEGRAM_CHAT_ID") or "6389082454"

def send_telegram_token_created(chat_id: str, token_number: str, service_name: str, office_type: str, wait_minutes: int = 10):
    """Sends detailed token generation alert with exact timestamp."""
    bot_token = get_bot_token()
    if not bot_token:
        return

    now_str = datetime.now().strftime("%I:%M:%S %p")
    msg_body = (
        f"🎫 <b>Smart Token System | தமிழ்நாடு அரசு</b>\n\n"
        f"📋 <b>TOKEN TICKET GENERATED</b>\n"
        f"• <b>Token Number:</b> <code>{token_number}</code>\n"
        f"• <b>Service:</b> {service_name}\n"
        f"• <b>Center:</b> {office_type.replace('_', ' ')}\n"
        f"• <b>Time Issued:</b> {now_str}\n"
        f"• <b>Est. Wait Time:</b> ~{wait_minutes} mins\n\n"
        f"<i>We will notify you here as soon as your counter is called!</i>"
    )
    _dispatch_to_targets(chat_id, msg_body)

def send_telegram_token_called(chat_id: str, token_number: str, counter_number: int, office_type: str):
    """Sends counter call alert with exact call timestamp."""
    bot_token = get_bot_token()
    if not bot_token:
        return

    now_str = datetime.now().strftime("%I:%M:%S %p")
    msg_body = (
        f"📣 <b>COUNTER ALERT: YOUR TOKEN IS CALLED!</b> 📣\n\n"
        f"• <b>Token Number:</b> <code>{token_number}</code>\n"
        f"• <b>Assigned Counter:</b> COUNTER {counter_number}\n"
        f"• <b>Call Time:</b> {now_str}\n"
        f"• <b>Center:</b> {office_type.replace('_', ' ')}\n\n"
        f"<b>Please proceed to Counter {counter_number} immediately.</b>\n"
        f"<i>Thank you for your patience!</i>"
    )
    _dispatch_to_targets(chat_id, msg_body)

def send_telegram_token_recalled(chat_id: str, token_number: str, office_type: str, status_note: str = "RECALLED"):
    """Sends recall/requeue notification if customer missed call."""
    bot_token = get_bot_token()
    if not bot_token:
        return

    now_str = datetime.now().strftime("%I:%M:%S %p")
    msg_body = (
        f"⚠️ <b>TOKEN ALERT: STATUS UPDATED ({status_note})</b>\n\n"
        f"• <b>Token Number:</b> <code>{token_number}</code>\n"
        f"• <b>Status:</b> {status_note}\n"
        f"• <b>Time:</b> {now_str}\n"
        f"• <b>Center:</b> {office_type.replace('_', ' ')}\n\n"
        f"<b>Notice:</b> If you missed your call, your service position has been updated or moved to the end of the queue. Please check the TV display or speak with an agent."
    )
    _dispatch_to_targets(chat_id, msg_body)

def _dispatch_to_targets(chat_id: str, msg_body: str):
    """Sends message to specified chat ID and default chat ID reliably."""
    target_ids = set()
    default_id = get_default_chat_id()
    
    if chat_id and str(chat_id).strip().isdigit():
        target_ids.add(str(chat_id).strip())
    if default_id:
        target_ids.add(str(default_id).strip())
        
    for cid in target_ids:
        try:
            _dispatch_telegram(cid, msg_body)
        except Exception as e:
            print(f"[TELEGRAM DISPATCH EXCEPTION] Failed for {cid}: {e}")

def _dispatch_telegram(chat_id: str, text_html: str):
    """Internal fail-safe Telegram API dispatcher."""
    bot_token = get_bot_token()
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text_html,
            "parse_mode": "HTML"
        }
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            print(f"[TELEGRAM SUCCESS] Sent notification to chat_id {chat_id}")
        else:
            print(f"[TELEGRAM WARNING] Telegram API returned status {res.status_code} for chat_id {chat_id}: {res.text}")
    except Exception as err:
        print(f"[TELEGRAM ERROR] Non-blocking dispatch error for chat_id {chat_id}: {err}")
