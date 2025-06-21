FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Create a non-root user and switch to it
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup
RUN chown -R appuser:appgroup /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8500
ENV LOG_LEVEL=INFO

# Expose the port
EXPOSE 8500

# Run the application
ENTRYPOINT ["./entrypoint.sh"]