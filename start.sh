#!/bin/bash

# Function to wait for ADB server
wait_for_adb_server() {
    local max_attempts=10
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if adb devices > /dev/null 2>&1; then
            return 0
        fi
        echo "Waiting for ADB server (attempt $attempt/$max_attempts)..."
        sleep 2
        attempt=$((attempt + 1))
    done
    return 1
}

# Kill any existing ADB server first
adb kill-server

# Start ADB server with root permissions and wait for it to be ready
adb -a -P 5037 start-server

# Wait for ADB server to be fully ready
if ! wait_for_adb_server; then
    echo "Failed to start ADB server"
    exit 1
fi

# Try to connect to the device multiple times
max_retries=5
retry_count=0
connected=false

while [ $retry_count -lt $max_retries ] && [ "$connected" = false ]; do
    if [ ! -z "$ADB_DEVICE_IP" ] && [ ! -z "$ADB_DEVICE_PORT" ]; then
        echo "Attempt $((retry_count + 1))/$max_retries: Connecting to device at $ADB_DEVICE_IP:$ADB_DEVICE_PORT"
        
        # First try to disconnect any existing connections
        adb disconnect "$ADB_DEVICE_IP:$ADB_DEVICE_PORT" > /dev/null 2>&1
        
        # Try to connect with TCP/IP mode
        adb tcpip 5555
        sleep 2
        
        # Try to connect
        if adb connect "$ADB_DEVICE_IP:$ADB_DEVICE_PORT" | grep -q "connected"; then
            # Wait a bit for the connection to stabilize
            sleep 2
            
            # Verify device is actually responding
            if adb devices | grep -q "$ADB_DEVICE_IP:$ADB_DEVICE_PORT.*device"; then
                connected=true
                echo "Successfully connected to device"
            else
                echo "Device connected but not responding"
                retry_count=$((retry_count + 1))
                [ $retry_count -lt $max_retries ] && sleep 5
            fi
        else
            echo "Connection attempt failed"
            retry_count=$((retry_count + 1))
            [ $retry_count -lt $max_retries ] && sleep 5
        fi
    else
        echo "ADB_DEVICE_IP or ADB_DEVICE_PORT not set"
        exit 1
    fi
done

if [ "$connected" = false ]; then
    echo "Failed to connect to device after $max_retries attempts"
    exit 1
fi

# Create necessary directories
mkdir -p /app/logs

# Change to app directory
cd /app

# Start the FastAPI application
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
