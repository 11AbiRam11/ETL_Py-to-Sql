import os
import subprocess
from datetime import datetime
from utils.send_email import send_mail

# Paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOAD_PSQL_PATH = os.path.join(project_root, "ETL", "Load_psql.py")
LOG_DIR = os.path.join(project_root, "logs")

# Ensure logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Timestamped log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(LOG_DIR, f"output_{timestamp}.txt")

# Run Load_psql.py and capture output
result = subprocess.run(["python", LOAD_PSQL_PATH], capture_output=True, text=True)

etl_output = result.stdout + "\n" + result.stderr

print(etl_output)

# Save output to log file
with open(log_file, "w", encoding="utf-8") as f:
    f.write(etl_output)

# Send email with latest ETL output
send_mail(body=etl_output)
