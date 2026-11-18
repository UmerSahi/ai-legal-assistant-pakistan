# Multi-stage production Dockerfile for Khan & Associates AI Legal Assistant
FROM python:3.12-slim AS base

# Install system dependencies for OCR and system monitoring
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source and data assets
COPY . .

# Ensure outputs directories exist
RUN mkdir -p outputs/indices outputs/drafts outputs/structured

# Expose API port
EXPOSE 8000

# Healthcheck configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production entrypoint
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
