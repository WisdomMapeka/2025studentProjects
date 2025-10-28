import uuid
import requests
from django.core.mail import get_connection, send_mail
from django.conf import settings
from notifications.models import Notification  # adjust import to your app
import socket

def send_custom_email(subject, message, recipient_list, queue=None, category='general'):
    """
    Sends an email using Django's email backend with a 5-second timeout.
    """
    try:
        # Create a mail connection with timeout
        connection = get_connection(timeout=5)  # 5 seconds timeout

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Sender email (set in settings.py)
            recipient_list,               # List of recipient emails
            fail_silently=False,          # Raise error if email fails
            connection=connection
        )

        # Save notification record (delivered)
        Notification.objects.create(
            user=queue.booking.citizen if queue else None,
            booking=queue.booking if queue else None,
            notification_type='email',
            category=category,
            subject=subject,
            message=message,
            delivered=True
        )

        return True

    except (socket.timeout, Exception) as e:
        print(f"Error sending email (timeout or other): {e}")

        # Save notification record (failed)
        Notification.objects.create(
            user=queue.booking.citizen if queue else None,
            booking=queue.booking if queue else None,
            notification_type='email',
            category=category,
            subject=subject,
            message=message,
            delivered=False
        )

        return False

    




def send_sms_via_api(phone_number, message, queue, category):
    """
    Sends an SMS via CODEL 2WayChat Bulk SMS API (v2).
    """

    api_url = "https://2wcapi.codel.tech/2wc/single-sms/v1/api"

    payload = {
        "token": settings.SMS_API_TOKEN,             # Your CODEL API Token     # Your registered Sender ID
        "destination": phone_number,                 # Example: 263777123123
        "messageText": message,                      # SMS content
        "messageReference": str(uuid.uuid4()),       # Unique message identifier
        "messageDate": "",                           # Optional field
        "messageValidity": "",                       # Optional field
        "sendDateTime": ""                           # Optional field
    }

    headers = {
        "Content-Type": "application/json"
    }
    print("Sending SMS with payload:", payload)
    try:
        response = requests.post(api_url, json=payload)

        data = response.text
        print("SMS sent successfully:", data)
        Notification.objects.create(
            user=queue.booking.citizen,
            booking=queue.booking,
            notification_type='sms',
            category=category,
            subject="SMS Delivered",
            message=message,
            delivered=True
        )
        return True

    except requests.RequestException as e:
        print(f"Error sending SMS via CODEL API: {e}")
        Notification.objects.create(
            user=queue.booking.citizen,
            booking=queue.booking,
            notification_type='sms',
            category=category,
            subject="SMS Delivery Failed",
            message=message,
            delivered=False
        )
        return False