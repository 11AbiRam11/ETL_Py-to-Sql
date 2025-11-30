import os
import subprocess
from datetime import datetime
import sys
import logging
import io

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.send_email import send_mail

# --- Logging Setup ---
# Get current time
now = datetime.now()

# Paths
LOG_DIR = os.path.join(project_root, "logs")

# Create month-wise log directory
log_month_dir = os.path.join(LOG_DIR, now.strftime("%Y-%m"))
os.makedirs(log_month_dir, exist_ok=True)

# Log filename for the current day
log_file = os.path.join(log_month_dir, f"{now.strftime('%Y-%m-%d')}.log")

# Create logger
logger = logging.getLogger("ETL_Logger")
logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# --- Handlers ---
# To prevent adding handlers multiple times in interactive sessions/imports
if not logger.handlers:
    # File handler (appends to the daily log)
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # In-memory text handler for capturing logs for the email
    log_stream = io.StringIO()
    memory_handler = logging.StreamHandler(log_stream)
    memory_handler.setFormatter(formatter)
    logger.addHandler(memory_handler)

# --- Main script ---
logger.info("Backfilling script started.")

# Paths
LOAD_PSQL_PATH = os.path.join(project_root, "ETL", "Load_psql.py")

# Top 20 Symmbols
symbols = [
    "NVDA",
    "AAPL",
    "GOOGL",
    "MSFT",
    "AMZN",
    "AVGO",
    "META",
    "TSM",
    "TSLA",
    "BRK-B",
    "LLY",
    "WMT",
    "JPM",
    "TCEHY",
    "V",
    "ORCL",
    "JNJ",
    "MA",
    "XOM",
    "IBM",
    "NFLX",
    "COST",
    "BABA",
]


for symbol in symbols:

    # Run Load_psql.py and log its output
    try:
        logger.info(f"Running subprocess")
        result = subprocess.run(
            ["python", LOAD_PSQL_PATH, symbol],
            capture_output=True,
            text=True,
            check=False,  # We check the returncode manually to log appropriately
            encoding="utf-8",
        )

        # Log stdout and stderr separately for clarity
        if result.stdout:
            logger.info("--- Subprocess STDOUT ---\n%s", result.stdout.strip())
        if result.stderr:
            logger.warning("--- Subprocess STDERR ---\n%s", result.stderr.strip())

        # Log non-zero exit codes as errors
        if result.returncode != 0:
            logger.error(
                f"Subprocess exited with a non-zero status: {result.returncode}"
            )

    except FileNotFoundError:
        logger.exception(f"Error: The script at {LOAD_PSQL_PATH} was not found.")
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred during subprocess execution. {e}"
        )

# # Send email with the captured logs from this run
# try:
#     logger.info("Preparing to send email notification.")
#     email_body = log_stream.getvalue()
#     if email_body:
#         send_mail(body=email_body)
#         logger.info("Email notification sent successfully.")
#     else:
#         logger.warning("Log stream was empty. Skipping email.")
# except Exception:
#     logger.exception("Failed to send email notification.")

# logger.info("ETL master script finished.")
