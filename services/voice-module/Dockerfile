# Voice Module Service Dockerfile
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

# Install system dependencies for audio processing with optimized settings
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    portaudio19-dev \
    python3-dev \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Configure pip for faster downloads using multiple mirrors
RUN pip config set global.index-url https://pypi.org/simple/ \
    && pip config set global.extra-index-url "https://pypi.python.org/simple/ https://files.pythonhosted.org/packages/" \
    && pip config set global.trusted-host "pypi.org pypi.python.org files.pythonhosted.org" \
    && pip config set global.timeout 300 \
    && pip config set global.retries 3

# Copy requirements first for better caching
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --parallel --upgrade -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p storage/audio storage/temp static

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]