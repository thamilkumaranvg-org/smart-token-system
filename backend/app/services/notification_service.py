import os
import logging
from datetime import datetime

logger = logging.getLogger("notification_service")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
TWILIO_SMS_NUMBER = os.getenv("TWILIO_SMS_NUMBER")

client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Twilio notification service initialized.")
    except Exception as e:
        logger.warning(f"Failed to initialize Twilio client: {e}")

def format_phone_number(phone_raw: str, is_whatsapp: bool = True) -> str:
    """Formats phone number string to E.164 / WhatsApp URI format."""
    phone_clean = "".join(filter(str.isdigit, phone_raw))
    if len(phone_clean) == 10:
        phone_clean = f"+91{phone_clean}"
    elif not phone_clean.startswith("+"):
        phone_clean = f"+{phone_clean}"
    
    return f"whatsapp:{phone_clean}" if is_whatsapp else phone_clean

def send_whatsapp_token_created(phone: str, token_number: str, service_name: str, office_type: str, wait_minutes: int = 10):
    """Sends detailed token creation WhatsApp message."""
    if not phone:
        return
    
    now_str = datetime.now().strftime("%I:%M:%S %p")
    msg_body = (
        f"🎫 Smart Token System | தமிழ்நாடு அரசு\n\n"
        f"📋 TOKEN TICKET GENERATED\n"
        f"• Token Number: {token_number}\n"
        f"• Service: {service_name}\n"
        f"• Center: {office_type.replace('_', ' ')}\n"
        f"• Time Issued: {now_str}\n"
        f"• Est. Wait Time: ~{wait_minutes} mins\n\n"
        f"We will notify you when your counter is ready!"
    )
    _dispatch_notification(phone, msg_body)

def send_whatsapp_token_called(phone: str, token_number: str, counter_number: int, office_type: str):
    """Sends detailed counter call WhatsApp message."""
    if not phone:
        return
    
    now_str = datetime.now().strftime("%I:%M:%S %p")
    msg_body = (
        f"📣 COUNTER ALERT: YOUR TOKEN IS CALLED! 📣\n\n"
        f"• Token Number: {token_number}\n"
        f"• Assigned Counter: COUNTER {counter_number}\n"
        f"• Call Time: {now_str}\n"
        f"• Center: {office_type.replace('_', ' ')}\n\n"
        f"Please proceed to Counter {counter_number} immediately!"
    )
    _dispatch_notification(phone, msg_body)

def send_whatsapp_token_recalled(phone: str, token_number: str, office_type: str, status_note: str = "RECALLED"):
    """Sends detailed recall/requeue WhatsApp message."""
    if not phone:
        return
    
    now_str = datetime.now().strftime("%I:%M:%S %p")
    msg_body = (
        f"⚠️ TOKEN ALERT: STATUS UPDATED ({status_note})\n\n"
        f"• Token Number: {token_number}\n"
        f"• Status: {status_note}\n"
        f"• Time: {now_str}\n"
        f"• Center: {office_type.replace('_', ' ')}\n\n"
        f"Notice: If you missed your call, your service position has been updated or moved to the end of the queue."
    )
    _dispatch_notification(phone, msg_body)

def _dispatch_notification(phone: str, message_body: str):
    """Internal fail-safe dispatcher supporting WhatsApp and SMS fallback."""
    digits_only = "".join(filter(str.isdigit, phone))
    if len(digits_only) < 10:
        print(f"[NOTIFICATION INFO] Skipping dispatch: customer_info '{phone}' does not contain a valid 10-digit phone number.")
        return

    if not client:
        print(f"[NOTIFICATION INFO] Simulated Alert to {phone}:\n{message_body}\n")
        return
    
    whatsapp_success = False
    try:
        formatted_wa = format_phone_number(phone, is_whatsapp=True)
        msg = client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=formatted_wa
        )
        print(f"[NOTIFICATION SUCCESS] WhatsApp alert dispatched SID: {msg.sid}")
        whatsapp_success = True
    except Exception as wa_err:
        print(f"[NOTIFICATION NOTICE] WhatsApp dispatch attempt note: {wa_err}")

    if not whatsapp_success and TWILIO_SMS_NUMBER:
        try:
            formatted_sms = format_phone_number(phone, is_whatsapp=False)
            sms_msg = client.messages.create(
                body=message_body,
                from_=TWILIO_SMS_NUMBER,
                to=formatted_sms
            )
            print(f"[NOTIFICATION SUCCESS] SMS alert dispatched SID: {sms_msg.sid}")
        except Exception as sms_err:
            print(f"[NOTIFICATION WARNING] SMS dispatch failed: {sms_err}")
