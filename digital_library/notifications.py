import os
import requests
from motor.motor_asyncio import AsyncIOMotorDatabase
from .models import Notification, User
from typing import Optional

EMAIL_API_URL = os.getenv("EMAIL_API_URL")
EMAIL_API_KEY = os.getenv("EMAIL_API_KEY")

async def send_notification(db: AsyncIOMotorDatabase, user: User, message: str, type: str, cc_user: Optional[User] = None):
    """
    Sends a notification via email and logs it to the database.
    """
    notification_collection = db.get_collection("notifications")
    notification_status = "pending"

    email_data = {
        "to": user.email,
        "subject": f"Update on your book: {type}",
        "body": message
    }
    if cc_user:
        email_data["cc"] = cc_user.email

    if EMAIL_API_URL and EMAIL_API_KEY:
        try:
            response = requests.post(
                EMAIL_API_URL,
                headers={"Authorization": f"Bearer {EMAIL_API_KEY}"},
                json=email_data
            )
            response.raise_for_status()
            notification_status = "sent"
        except requests.exceptions.RequestException as e:
            print(f"Failed to send email: {e}")
            notification_status = "failed"
    else:
        print("--- MOCK EMAIL ---")
        print(f"To: {email_data['to']}")
        if "cc" in email_data:
            print(f"Cc: {email_data['cc']}")
        print(f"Subject: {email_data['subject']}")
        print(f"Body: {email_data['body']}")
        print("--------------------")
        notification_status = "sent_mock"


    notification = {
        "user_id": user.id,
        "message": message,
        "type": type,
        "status": notification_status
    }
    await notification_collection.insert_one(notification)
