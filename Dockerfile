# Stage 1: Android SDK and Tools
FROM ubuntu:22.04 AS android-sdk

# Install required packages
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    openjdk-11-jdk \
    && rm -rf /var/lib/apt/lists/*

# Download and install Android SDK
ENV ANDROID_HOME=/opt/android-sdk
RUN mkdir -p ${ANDROID_HOME} && cd ${ANDROID_HOME} && \
    wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip && \
    unzip commandlinetools-linux-*_latest.zip && \
    rm commandlinetools-linux-*_latest.zip && \
    mkdir -p ${ANDROID_HOME}/cmdline-tools/latest && \
    mv ${ANDROID_HOME}/cmdline-tools/* ${ANDROID_HOME}/cmdline-tools/latest/ || true

# Set PATH
ENV PATH=${PATH}:${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools

# Accept licenses and install required packages
RUN yes | sdkmanager --licenses && \
    sdkmanager "platform-tools" "build-tools;33.0.0" "platforms;android-33"

# Stage 2: Python Application
FROM python:3.9-slim

# Copy Android SDK from previous stage
COPY --from=android-sdk /opt/android-sdk /opt/android-sdk
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=${PATH}:${ANDROID_HOME}/platform-tools

# Install required system packages
RUN apt-get update && apt-get install -y \
    adb \
    android-tools-adb \
    usbutils \
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

# Expose FastAPI and ADB ports
EXPOSE 8000
EXPOSE 5037

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBUG=1

# Create volume mount points
VOLUME ["/app/logs", "/app/accounts", "/app/data"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
