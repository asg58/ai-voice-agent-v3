#!/bin/bash

# =============================================================================
# DOCKER OPTIMIZATION SCRIPT - Fast Downloads & Builds
# =============================================================================
# This script optimizes Docker builds for faster downloads and builds

echo "🚀 Optimizing Docker environment for faster downloads..."

# Set Docker buildkit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Configure Docker daemon for performance
cat > /tmp/docker-daemon.json << 'EOF'
{
  "experimental": true,
  "features": {
    "buildkit": true
  },
  "builder": {
    "gc": {
      "enabled": true,
      "defaultKeepStorage": "20GB"
    }
  },
  "registry-mirrors": [
    "https://registry-1.docker.io"
  ],
  "insecure-registries": [],
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
EOF

echo "📦 Optimizing package managers..."

# Create optimized apt configuration
cat > config/apt.conf << 'EOF'
APT::Acquire::Retries "3";
APT::Acquire::http::Timeout "300";
APT::Acquire::https::Timeout "300";
APT::Acquire::ftp::Timeout "300";
APT::Acquire::ForceIPv4 "true";
APT::Install-Recommends "false";
APT::Install-Suggests "false";
Acquire::Languages "none";
EOF

# Create optimized pip configuration
cat > config/pip.conf << 'EOF'
[global]
index-url = https://pypi.org/simple/
extra-index-url = https://pypi.python.org/simple/
                  https://files.pythonhosted.org/packages/
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
timeout = 300
retries = 3
disable-pip-version-check = true
prefer-binary = true
no-cache-dir = false
parallel-downloads = true
EOF

echo "🔧 Optimizing Docker Compose builds..."

# Build all services with optimized settings
docker-compose build \
  --parallel \
  --compress \
  --force-rm \
  --no-cache \
  --pull

echo "✅ Docker optimization complete!"
echo "🎯 Next steps:"
echo "   - Use 'docker-compose up --build' for rebuilding"
echo "   - Use 'docker-compose build --parallel' for parallel builds"
echo "   - Monitor build times with 'time docker-compose build'"
