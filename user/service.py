from django.core.mail import EmailMessage
from django.conf import settings
from cryptography.fernet import Fernet
import random
from django.utils import timezone


key=b'njVD0FDf5dqAJ7YREQRNVXRUQ39XmK29uIqz357Jj0s='
fernet=Fernet(key)

def send_verification_email(email, token):
    try:
        subject = "Gaytri Farm - Verify Your Email Address"
        html_content=f"""
        Hi there,<br><br>
        Thank you for Signup <b>Gaytri Farm</b><br><br>
        Your email verification code is: <b>{token}</b>
        """
        email = EmailMessage(subject, html_content, settings.DEFAULT_FROM_EMAIL, [email])
        email.content_subtype = 'html'

        res=email.send()
        return res
    except Exception as e:
        print(f"Error sending email: {e}")
        return None
    
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
    try:
        subject = 'Reset Your Password'
        html_content = f"""
        <p>Hello,</p>
        <p>Your password reset token for GaytriFarm is : <b>{token}</b><p>
        """
        email = EmailMessage(subject, html_content, settings.DEFAULT_FROM_EMAIL, [email])
        email.content_subtype = 'html'
        res=email.send()
        return res
    except:
        return None

