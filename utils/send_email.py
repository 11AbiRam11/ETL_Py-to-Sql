import smtplib
from dotenv import load_dotenv
import os
from email.message import EmailMessage
from datetime import datetime
import ssl
import logging

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Load .env file ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(project_root, "Config", ".env")

logger.info(f"Attempting to load .env")

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logger.info(".env file found and loaded successfully.")
else:
    load_dotenv()  # fallback to default search
    logger.warning(f".env not found at {dotenv_path}. Loaded from default location.")

# --- Configuration ---
SENDER_EMAIL = os.getenv("sender_email")
RECEIVER_EMAIL = os.getenv("receiver_email")
PASSWORD = os.getenv("email_app_passwd")

# FIX: Missing SMTP server & port
SMTP_SERVER = os.getenv("smtp_server", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("smtp_port", 587))


def send_mail(body: str):
    """
    Sends an email using SMTP with TLS encryption.
    Raises an exception if configuration or sending fails.
    """

    # Validate all config variables
    if not all([SENDER_EMAIL, RECEIVER_EMAIL, PASSWORD]):
        logger.error("Missing email configuration variables.")
        raise ValueError(
            "Missing required .env variables: sender_email, receiver_email, email_app_passwd"
        )

    current_datetime = datetime.now()

    msg = EmailMessage()
    msg["Subject"] = "Python Automated ETL Pipeline"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    msg.set_content(
        f"ETL Pipeline executed on: {current_datetime}\n\n"
        f"Below are the details:\n{body}"
    )

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, PASSWORD)
            server.send_message(msg)

        logger.info("Email successfully sent!")

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise
