# ─────────────── BUILD STAGE ───────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install `uv`
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Create lock file if it doesn't exist
RUN uv lock

# Create virtual environment and install dependencies
RUN uv venv && \
    uv pip install --upgrade pip && \
    uv pip install playwright && \
    uv sync --frozen --no-cache && \
    find .venv -name '*.pyc' -delete && \
    find .venv -name '__pycache__' -type d -exec rm -rf {} +

# Copy application code
COPY app ./app

# ─────────────── RUNTIME STAGE ───────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Create non-root user
RUN adduser \
    --disabled-password \
    --gecos "" \
    --uid 1001 \
    appuser

WORKDIR /app

# Copy necessary files from builder
COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/app ./app

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Run FastAPI with Uvicorn
CMD ["/app/.venv/bin/gunicorn", "app.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers=2"]
