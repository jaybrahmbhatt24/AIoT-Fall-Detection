import os
import importlib
import alerts  # Import first to get the module

# Set environment variables
os.environ["TWILIO_SID"] = "ACb757c57b085106c93b50df19943c38e2"
os.environ["TWILIO_AUTH"] = "e1fd53e5526c0a42075aa16127b0a91e"
os.environ["TWILIO_SMS_NUMBER"] = "+15412292556"
os.environ["EMERGENCY_PHONE"] = "+917434984735"

# Reload the alerts module to re-initialize with the new environment variables
importlib.reload(alerts)
from alerts import send_sms, send_whatsapp, make_call

def test_alerts():
    test_message = "[TEST] This is a test alert from the fall detection system."
    
    print("Sending test SMS...")
    send_sms(test_message)
    
    # Skip WhatsApp test since we don't have a WhatsApp number configured
    # print("\nSending test WhatsApp message...")
    # send_whatsapp(test_message)
    
    print("\nInitiating test call...")
    make_call(test_message)
    
    print("\nTest alerts completed. Check your phone for messages and calls.")

if __name__ == "__main__":
    test_alerts()