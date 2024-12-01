FROM python:3.9-slim

# Install necessary tools
RUN apt-get update && apt-get install -y \
    adb \
    android-tools-adb \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data

# Expose FastAPI port
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBUG=1

# Create volume mount points
VOLUME ["/app/logs", "/app/accounts", "/app/data"]

# Create startup script
RUN echo '#!/bin/bash\n\
# Kill any existing ADB server\n\
adb kill-server\n\
\n\
# Start ADB server to listen on all interfaces\n\
adb -a nodaemon server start &\n\
\n\
# Start FastAPI application\n\
uvicorn api.main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["/app/start.sh"]
