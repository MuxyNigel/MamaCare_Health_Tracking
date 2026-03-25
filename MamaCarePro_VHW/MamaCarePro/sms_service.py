# sms_service.py
from twilio.rest import Client
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

class SMSService:
    def __init__(self):
        self.client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.phone_number = os.getenv('TWILIO_PHONE')
    
    def send_appointment_reminder(self, phone, appointment_date, appt_type):
        """Send appointment reminder SMS"""
        message = f"Reminder: Your {appt_type} visit is on {appointment_date}. Please attend. - MaternalCare"
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=phone
            )
            return {"success": True, "sid": message.sid}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_high_risk_alert(self, phone, risk_level):
        """Send high-risk alert SMS"""
        if risk_level == "High":
            message = "⚠️ HIGH RISK ALERT: Please see a healthcare provider immediately. - MaternalCare"
        else:
            message = f"⚠️ RISK ALERT: Risk level is {risk_level}. Please follow up with your healthcare provider. - MaternalCare"
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=phone
            )
            return {"success": True, "sid": message.sid}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Test SMS service
try:
    sms_service = SMSService()
    print("✅ SMS Service initialized!")
except:
    print("⚠️ SMS Service failed to initialize (check credentials)")

# Mock SMS for development
class MockSMSService:
    def send_appointment_reminder(self, phone, appointment_date, appt_type):
        print(f"MOCK SMS to {phone}: Reminder for {appt_type} on {appointment_date}")
        return {"success": True, "sid": "mock_sid"}
    
    def send_high_risk_alert(self, phone, risk_level):
        print(f"MOCK SMS to {phone}: Risk alert - {risk_level}")
        return {"success": True, "sid": "mock_sid"}

# Use mock if real credentials not available
try:
    sms_service = SMSService()
except:
    sms_service = MockSMSService()
    print("Using mock SMS service for development")