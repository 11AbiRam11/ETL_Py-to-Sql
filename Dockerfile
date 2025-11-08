# ---------- Base Image ----------
FROM python:3.11-slim

# ---------- Set Working Directory ----------
WORKDIR /app

# ---------- Copy and Install Dependencies ----------
COPY Config/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Copy Entire Project ----------
COPY . .

# ---------- Environment Variables ----------
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Kolkata

# ---------- Default Command ----------
CMD ["python", "etl/master.py"]
