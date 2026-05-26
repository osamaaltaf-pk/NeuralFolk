# ==========================================
# Stage 1: Build dependencies using uv
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies needed for compiling binary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for rapid package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependencies list
COPY requirements.txt .

# Install dependencies into system site-packages (safe in this container stage)
RUN uv pip install --system -r requirements.txt

# ==========================================
# Stage 2: Minimal runtime image
# ==========================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install curl in runtime for docker-compose healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed site-packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user for security compliance
RUN groupadd -g 10001 neuralfolk && \
    useradd -u 10001 -g neuralfolk -m -s /bin/bash neuralfolk && \
    chown -R neuralfolk:neuralfolk /app

# Copy application files (ensure owner is non-root)
COPY --chown=neuralfolk:neuralfolk . .

USER neuralfolk

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
