# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Create non-root user
RUN useradd -u 10001 -m appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD python -c "import requests; import os; import sys; import time;\nimport urllib.request as r;\nimport json;\n\ntry:\n  resp = r.urlopen('http://127.0.0.1:8000/health', timeout=2)\n  sys.exit(0 if resp.getcode()==200 else 1)\nexcept Exception:\n  sys.exit(1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


