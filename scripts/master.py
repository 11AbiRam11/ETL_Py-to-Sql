import os
import subprocess
from datetime import datetime
import sys

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.send_email import send_mail

# Paths
LOAD_PSQL_PATH = os.path.join(project_root, "ETL", "Load_psql.py")
LOG_DIR = os.path.join(project_root, "logs")

# Get current time
now = datetime.now()

# Create month-wise log directory
log_month_dir = os.path.join(LOG_DIR, now.strftime("%Y-%m"))
os.makedirs(log_month_dir, exist_ok=True)

# Timestamped log filename
timestamp = now.strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_month_dir, f"output_{timestamp}.txt")

# Run Load_psql.py and capture output
result = subprocess.run(["python", LOAD_PSQL_PATH], capture_output=True, text=True)

etl_output = result.stdout + "\n" + result.stderr

print(etl_output)

# Save output to log file
with open(log_file, "w", encoding="utf-8") as f:
    f.write(etl_output)

# Send email with latest ETL output
send_mail(body=etl_output)
