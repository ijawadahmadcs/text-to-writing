FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for opencv-python-headless and Pillow
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY python/requirements.txt ./python/requirements.txt
RUN pip install --no-cache-dir -r python/requirements.txt

# Copy only what the backend needs
COPY python/ ./python/
COPY public/fonts/ ./public/fonts/
COPY public/templates/ ./public/templates/

WORKDIR /app/python

CMD gunicorn dev_server:app --bind 0.0.0.0:${PORT:-5328} --workers 2 --timeout 120
