FROM python:3.9.2-slim-buster
RUN mkdir /app && chmod 777 /app
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
RUN apt -qq update && apt -qq install -y git python3 python3-pip ffmpeg
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt
CMD ["bash","bash.sh"]


FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (important for cryptography & speed)
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip & install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install tgcrypto  # faster crypto if using Pyrogram

# Copy bot code
COPY . .

# Environment variables will be set in Render dashboard
ENV PYTHONUNBUFFERED=1

# Run the bot (adjust filename if yours is different, e.g. main.py or bot.py)
CMD ["bash", "bash.sh"]
