FROM oculair/virtualinfluencer:api-improvements

# Install FastAPI and dependencies
RUN pip install --no-cache-dir \
    fastapi==0.115.5 \
    uvicorn==0.32.1 \
    pydantic==2.10.2 \
    PyYAML==6.0.1 \
    psutil==5.9.8 \
    ruamel.yaml==0.18.5 \
    aiofiles==23.2.1

# Create API directory and files
WORKDIR /app

# Copy all necessary files
COPY api /app/api
COPY GramAddict /app/GramAddict
COPY run.py /app/run.py
COPY accounts /app/accounts
COPY requirements.txt /app/requirements.txt

# Install requirements
RUN pip install -r /app/requirements.txt

# Ensure __init__.py exists in all necessary directories
RUN touch /app/__init__.py && \
    touch /app/api/__init__.py && \
    touch /app/api/services/__init__.py && \
    touch /app/api/routers/__init__.py

# Set Python path to include app directory
ENV PYTHONPATH=/app

# Create start.sh script with proper line endings
RUN echo '#!/bin/bash\n\
\n\
# Start ADB server\n\
adb start-server\n\
\n\
# Check if ADB_DEVICE_IP and ADB_DEVICE_PORT are set\n\
if [ -n "$ADB_DEVICE_IP" ] && [ -n "$ADB_DEVICE_PORT" ]; then\n\
    echo "Connecting to device at $ADB_DEVICE_IP:$ADB_DEVICE_PORT"\n\
    adb connect $ADB_DEVICE_IP:$ADB_DEVICE_PORT\n\
fi\n\
\n\
cd /app && uvicorn api.main:app --host 0.0.0.0 --port 8000 --log-level debug\n' | tr -d '\r' > /app/start.sh

# Make start.sh executable
RUN chmod +x /app/start.sh

EXPOSE 8000 5037

CMD ["/app/start.sh"]
