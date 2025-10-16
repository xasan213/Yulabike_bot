FROM python:3.11-slim

# Minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Run bot directly (no GUI required)
CMD ["python", "bot.py"]
