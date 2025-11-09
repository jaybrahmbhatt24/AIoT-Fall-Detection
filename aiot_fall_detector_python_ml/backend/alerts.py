import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Twilio configuration - hardcoded values
TWILIO_SID = "ACb757c57b085106c93b50df19943c38e2"
TWILIO_AUTH = "e1fd53e5526c0a42075aa16127b0a91e"
TWILIO_SMS_NUMBER = "+15412292556"
EMERGENCY_PHONE = "+917434984735"  # Your emergency contact number

# Initialize Twilio client if credentials are available
client: Optional[Client] = None
if TWILIO_SID and TWILIO_AUTH:
    client = Client(TWILIO_SID, TWILIO_AUTH)
else:
    print("[WARNING] Twilio not properly configured. Check your environment variables.")

def send_sms(text: str) -> None:
    """
    Send an SMS message to the emergency contact number.
    
    Args:
        text: The message text to send
    """
    if not client or not TWILIO_SMS_NUMBER or not EMERGENCY_PHONE:
        print("[SMS] Twilio not properly configured. Check environment variables.")
        return
    
    try:
        message = client.messages.create(
            body=text, 
            from_=TWILIO_SMS_NUMBER, 
            to=EMERGENCY_PHONE
        )
        print(f"[SMS] Message sent. SID: {message.sid}")
    except TwilioRestException as e:
        print(f"[SMS] Failed to send message: {str(e)}")

def send_whatsapp(text: str) -> None:
    """
    Send a WhatsApp message (not configured in current setup).
    
    Args:
        text: The message text to send
    """
    print("[WhatsApp] WhatsApp notifications are not configured in this setup.")
    print("To enable WhatsApp, set up TWILIO_WHATSAPP_NUMBER in your environment.")

def make_call(text: str) -> None:
    """
    Make a voice call to the emergency contact number.
    
    Args:
        text: The message to be read during the call
    """
    if not client or not TWILIO_SMS_NUMBER or not EMERGENCY_PHONE:
        print("[CALL] Twilio not properly configured. Check environment variables.")
        return
    
    try:
        from urllib.parse import quote
        twiml_url = f"http://twimlets.com/message?Message%5B0%5D={quote(text)}"
        call = client.calls.create(
            url=twiml_url,
            from_=TWILIO_SMS_NUMBER,
            to=EMERGENCY_PHONE
        )
        print(f"[CALL] Call initiated. SID: {call.sid}")
    except Exception as e:
        print(f"[CALL] Failed to initiate call: {str(e)}")
