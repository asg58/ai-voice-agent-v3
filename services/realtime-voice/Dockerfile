# =============================================================================
# ENTERPRISE AI VOICE AGENT - PRODUCTION DOCKERFILE
# =============================================================================
# Multi-stage build for optimized production image
# Supports both CPU and GPU deployments
# Base image: Python 3.11 with optimizations

# === BUILD STAGE ===
FROM python:3.11-slim AS builder

# Set build arguments
ARG ENVIRONMENT=production
ARG INSTALL_DEV=false

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Configure faster mirrors for package downloads
RUN echo "deb http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list \
    && echo "deb http://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list \
    && echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

# Install system dependencies for building with parallel downloads
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    git \
    curl \
    wget \
    libffi-dev \
    libssl-dev \
    libsndfile1 \
    ffmpeg \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r voiceai && useradd -r -g voiceai voiceai

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements*.txt ./

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

# Configure pip for faster downloads using config file and additional optimizations
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip config set global.parallel-downloads true && \
    pip config set global.prefer-binary true && \
    if [ "$INSTALL_DEV" = "true" ]; then \
        pip install -r requirements-dev.txt; \
    else \
        # Install weaviate-client and other critical dependencies explicitly
        pip install -r requirements-weaviate.txt; \
        # Verify weaviate is installed correctly
        python -c "import weaviate; print(f'Weaviate client installed: {weaviate.__version__}')"; \
        # Install other dependencies
        pip install --no-cache-dir ollama>=0.1.0 psutil uvicorn==0.24.0 fastapi==0.104.1 numpy==1.24.3; \
        # Install PyAudio with all build dependencies available
        pip install --no-cache-dir pyaudio==0.2.11; \
    fi

# === RUNTIME STAGE ===
FROM python:3.11-slim AS runtime

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8080 \
    WORKERS=4 \
    WORKER_CLASS=uvicorn.workers.UvicornWorker

# Configure faster mirrors for runtime downloads
RUN echo "deb http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list \
    && echo "deb http://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list \
    && echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

# Copy requirements-weaviate.txt for runtime installation
COPY requirements-weaviate.txt /tmp/requirements-weaviate.txt

# Install runtime system dependencies with faster mirrors
RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2 \
    libsndfile1 \
    ffmpeg \
    curl \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/* \
    # Configure pip for faster downloads
    && pip config set global.index-url https://pypi.org/simple/ \
    && pip config set global.extra-index-url "https://pypi.python.org/simple/ https://files.pythonhosted.org/packages/" \
    && pip config set global.trusted-host "pypi.org pypi.python.org files.pythonhosted.org" \
    && pip config set global.timeout 300 \
    && pip config set global.retries 3 \
    # Install weaviate-client and other critical dependencies with parallel downloads
    && pip install --upgrade pip \
    && pip install -r /tmp/requirements-weaviate.txt \
    && python -c "import weaviate; print(f'Weaviate client installed in runtime: {weaviate.__version__}')" \
    # Install other dependencies with optimized settings
    && pip install --no-cache-dir --upgrade psutil uvicorn==0.24.0 fastapi==0.104.1 numpy==1.24.3 ollama>=0.1.0

# Create non-root user
RUN groupadd -r voiceai && useradd -r -g voiceai voiceai

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=voiceai:voiceai ./main.py ./main.py
COPY --chown=voiceai:voiceai ./main_production.py ./main_production.py
COPY --chown=voiceai:voiceai ./src ./src
COPY --chown=voiceai:voiceai ./scripts ./scripts
COPY --chown=voiceai:voiceai ./storage ./storage
COPY --chown=voiceai:voiceai ./.env.example ./.env
COPY --chown=voiceai:voiceai ./check_dependencies.py ./check_dependencies.py
COPY --chown=voiceai:voiceai ./docker-entrypoint.sh ./docker-entrypoint.sh
COPY --chown=voiceai:voiceai ./requirements-weaviate.txt ./requirements-weaviate.txt

# Create necessary directories and make entrypoint script executable
RUN mkdir -p /app/logs /app/storage/temp /app/storage/models \
    && chmod +x /app/docker-entrypoint.sh \
    && chown -R voiceai:voiceai /app

# Switch to non-root user
USER voiceai

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
ENTRYPOINT ["/app/docker-entrypoint.sh"]