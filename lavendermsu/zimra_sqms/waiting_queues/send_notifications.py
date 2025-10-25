from django.core.mail import send_mail
from django.conf import settings

def send_custom_email(subject, message, recipient_list):
    """
    Sends an email using Django's email backend.
    """
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Sender email (set in settings.py)
            recipient_list,               # List of recipient emails
            fail_silently=False,          # Raise error if email fails
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False