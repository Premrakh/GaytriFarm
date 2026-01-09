from django.core.mail import send_mail
from cryptography.fernet import Fernet
import random
from django.utils import timezone
from django.conf import settings

key=b'njVD0FDf5dqAJ7YREQRNVXRUQ39XmK29uIqz357Jj0s='
fernet=Fernet(key)


def send_verification_email(email, token):
    subject = "Gaytri Farm - Verify Your Email Address"
    message = f"""
    Hi there,
    
    Thank you for signing up for Gaytri Farm!
    
    Your email verification code is: {token}
    
    Best regards,
    Gaytri Farm Team
    """
    html_message = f"""
    <p>Hi there,</p>
    <p>Thank you for signing up for <b>Gaytri Farm</b>!</p>
    <p>Your email verification code is: <b>{token}</b></p>
    <p>Best regards,<br>Gaytri Farm Team</p>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Verification email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

    
def generate_token(user_id):
    token =  str(random.randint(10000,99999)) + '--' +  str(timezone.now()+timezone.timedelta(minutes=5))  + '--' + str(user_id)
    encrypted_token = fernet.encrypt(token.encode()).decode()
    return encrypted_token

def unzip_token(token):
    try:
        decrypted_token = fernet.decrypt(token.encode()).decode()
        parts = decrypted_token.split("--")
        expiry_time_str = parts[1]
        expiry_time = timezone.datetime.fromisoformat(expiry_time_str)

        if timezone.now() > expiry_time:
            return None, "expired_token"
        user_id = parts[-1]
        return user_id, None
    except Exception as e:
        return None, "invalid_token"



def send_forgot_password_email(email, token):
    subject = 'Gaytri Farm - Reset Your Password'
    message = f"""
    Hello,
    
    Your password reset token for Gaytri Farm is: {token}
    
    If you did not request a password reset, please ignore this email.
    
    Best regards,
    Gaytri Farm Team
    """
    html_message = f"""
    <p>Hello,</p>
    <p>Your password reset token for <b>Gaytri Farm</b> is: <b>{token}</b></p>
    <p>If you did not request a password reset, please ignore this email.</p>
    <p>Best regards,<br>Gaytri Farm Team</p>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Password reset email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

