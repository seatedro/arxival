FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs /app/papers /app/cache

ENV PYTHONUNBUFFERED=1
CMD ["python", "cron_batch.py", "--max-papers", "50"]
