FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user and switch to it
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup
RUN chown -R appuser:appgroup /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8300
ENV LOG_LEVEL=INFO

# Expose the port
EXPOSE 8300

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8300"]