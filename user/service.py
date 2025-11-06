from django.core.mail import EmailMessage
from cryptography.fernet import Fernet
import random
from django.utils import timezone
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings

key=b'njVD0FDf5dqAJ7YREQRNVXRUQ39XmK29uIqz357Jj0s='
fernet=Fernet(key)

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = settings.EMAIL_HOST_PASSWORD

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
    sib_api_v3_sdk.ApiClient(configuration)
)


def send_verification_email(email, token):
    subject = "Gaytri Farm - Verify Your Email Address"
    html_content=f"""
    Hi there,<br><br>
    Thank you for Signup <b>Gaytri Farm</b><br><br>
    Your email verification code is: <b>{token}</b>
    """
    sender = {"name": "Gaytri Farm", "email": settings.DEFAULT_FROM_EMAIL}
    to = [{"email": email}]

    email_data = {
        "sender": sender,
        "to": to,
        "subject": subject,
        "htmlContent": html_content
    }
    try:
        api_instance.send_transac_email(email_data)
        print(f"Verification email sent successfully to {email}")
        return True
    except ApiException as e:
        print(f"Error sending Brevo email: {e}")
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
    html_content = f"""
    <p>Hello,</p>
    <p>Your password reset token for GaytriFarm is : <b>{token}</b><p>
    """
    sender = {"name": "Gaytri Farm", "email": settings.DEFAULT_FROM_EMAIL}
    to = [{"email": email}]

    email_data = {
        "sender": sender,
        "to": to,
        "subject": subject,
        "htmlContent": html_content
    }
    try:
        api_instance.send_transac_email(email_data)
        print(f"Verification email sent successfully to {email}")
        return True
    except ApiException as e:
        print(f"Error sending Brevo email: {e}")
        return False

