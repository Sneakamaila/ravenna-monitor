FROM python:3.12-slim

# Prevent python from buffering stdout/stderr and writing pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Create non-root user for security
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY main.py .

# Create data directory for persistent state and set permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

ENV STATE_FILE_PATH=/app/data/seen_offers.json \
    WEB_HOST=0.0.0.0 \
    WEB_PORT=8080

EXPOSE 8080

CMD ["python", "main.py"]
