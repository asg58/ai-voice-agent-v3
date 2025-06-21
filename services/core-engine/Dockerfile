# Core Engine Service Dockerfile
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Configure faster mirrors for package downloads
RUN echo "deb http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list \
    && echo "deb http://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list \
    && echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

# Install system dependencies with optimized settings
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./

# Configure pip for faster downloads with optimized settings
RUN echo "[global]" > /etc/pip.conf && \
    echo "index-url = https://pypi.org/simple/" >> /etc/pip.conf && \
    echo "extra-index-url = https://pypi.python.org/simple/" >> /etc/pip.conf && \
    echo "                  https://files.pythonhosted.org/packages/" >> /etc/pip.conf && \
    echo "trusted-host = pypi.org" >> /etc/pip.conf && \
    echo "               pypi.python.org" >> /etc/pip.conf && \
    echo "               files.pythonhosted.org" >> /etc/pip.conf && \
    echo "timeout = 300" >> /etc/pip.conf && \
    echo "retries = 3" >> /etc/pip.conf && \
    echo "disable-pip-version-check = true" >> /etc/pip.conf && \
    echo "prefer-binary = true" >> /etc/pip.conf && \
    echo "no-cache-dir = false" >> /etc/pip.conf && \
    echo "parallel-downloads = true" >> /etc/pip.conf

# Configure pip for faster downloads
RUN pip config set global.parallel-downloads true \
    && pip config set global.prefer-binary true

# Install dependencies with optimized parallel downloads
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]