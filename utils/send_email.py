import smtplib
from dotenv import load_dotenv
import os
from email.message import EmailMessage
from datetime import datetime
import ssl
from os.path import join, dirname

BASE_DIR = dirname(__file__)

DOTENV_PATH = join(BASE_DIR, "..", "config", ".env")

# Load variables from the .env file
load_dotenv(dotenv_path=DOTENV_PATH)


load_dotenv()

# --- Configuration ---
SENDER_EMAIL = os.getenv("sender_email")
RECEIVER_EMAIL = os.getenv("receiver_email")
PASSWORD = os.getenv("email_app_passwd")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_mail(body: str):
    """
    Sends an email with the provided body content.
    """
    current_datetime = datetime.now()  # accurate timestamp

    msg = EmailMessage()
    msg["Subject"] = "Python Automated ETL Pipeline"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    msg.set_content(
        f"The ETL Pipeline has run on {current_datetime}\n"
        f"Following are the output details:\n\n{body}"
    )
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, PASSWORD)
            server.send_message(msg)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")


# if __name__ == "__main__":
#     send_mail(body="This is test")
