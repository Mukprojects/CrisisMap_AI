FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system --gid 1001 crisismap \
    && adduser --system --uid 1001 --gid 1001 --no-create-home crisismap

# Copy dependency files
COPY pyproject.toml ./
COPY crisismap_ai/requirements.txt ./crisismap_ai/

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -e . \
    && pip install gunicorn

# Copy application code
COPY . .

# Set ownership and permissions
RUN chown -R crisismap:crisismap /app
USER crisismap

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "crisismap_ai.api.app:app"]