FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /

# Copy application code
# COPY ./.env ./.env
# COPY app/ app/

# CMD ["python", "-m", "app.main"]
