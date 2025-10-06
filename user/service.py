from django.core.mail import EmailMessage
from django.conf import settings
from cryptography.fernet import Fernet
import random
from django.utils import timezone


key=b'njVD0FDf5dqAJ7YREQRNVXRUQ39XmK29uIqz357Jj0s='
fernet=Fernet(key)

def send_verification_email(email, token):
    try:
        subject = 'Please Verify Your Email Address'
        html_content=f"<strong>Verification Code: {token}</strong>"
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
        <p>You're receiving this email because you requested a password reset for your user account at Snowvue.</p>
        <p>Please go to the following page and choose a new password: <a href="{settings.FRONTEND_URL}/auth?token={token}&type=reset-password&value={email}&via=email">Click_me</a></p>
        <p>Your username, in case you’ve forgotten: {email}</p>
        <p>Thanks for using our site!</p>
        <p>The Snowvue team</p>
        """
        email = EmailMessage(subject, html_content, settings.DEFAULT_FROM_EMAIL, [email])
        email.content_subtype = 'html'
        res=email.send()
        return res
    except:
        return None

