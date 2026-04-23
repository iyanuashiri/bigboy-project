import logging
import requests
from django.conf import settings


logger = logging.getLogger(__name__)


def send_whatsapp_message(to_number, body_text):
    """
    Sends a message using Meta's WhatsApp Cloud API.
    to_number: should be in format '2348012345678' (no '+' prefix)
    """
    url = f"https://graph.facebook.com/{settings.META_API_VERSION}/{settings.META_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {settings.META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number.replace("+", ""), # Meta prefers no '+'
        "type": "text",
        "text": {"preview_url": False, "body": body_text},
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Message sent to {to_number}")
        print(  f"Message sent to {to_number}"  )
        return response.json()
    except Exception as e:
        logger.error(f"Meta API Error: {e.response.text if hasattr(e, 'response') else str(e)}")
        return None