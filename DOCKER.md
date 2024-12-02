# Docker Container Documentation

## Overview
The Virtual Influencer Docker container provides an automated Instagram interaction system with a FastAPI backend and ADB integration for device control.

## Container Information
- **Image Name**: `oculair/virtualinfluencer`
- **Latest Tag**: `1.0.0`
- **Docker Hub**: [oculair/virtualinfluencer](https://hub.docker.com/r/oculair/virtualinfluencer)

## Quick Start
```bash
# Pull the image
docker pull oculair/virtualinfluencer:latest

# Run with docker-compose
docker-compose up -d
```

## Environment Variables
Required environment variables in `.env` file:
```env
NOCODB_BASE_URL=<nocodb_url>
NOCODB_TOKEN=<your_token>
NOCODB_PROJECT_ID=<project_id>
NOCODB_HISTORY_FILTERS_TABLE_ID=<table_id>
NOCODB_HISTORY_FILTERS_VIEW_ID=<view_id>
NOCODB_INTERACTED_USERS_TABLE_ID=<table_id>
NOCODB_INTERACTED_USERS_VIEW_ID=<view_id>
```

## Port Mappings
- **8000**: FastAPI application port
  - Health check endpoint: `http://localhost:8000/health`
  - API documentation: `http://localhost:8000/docs`

## Volume Mounts
- `/app/logs`: Container logs directory
- `/app/accounts`: Instagram account configurations
- `/app/data`: Application data storage
- `${USERPROFILE}/.android`: ADB keys for device authentication

## Docker Compose Configuration
```yaml
version: '3.8'

services:
  virtualinfluencer:
    image: oculair/virtualinfluencer:latest
    container_name: virtualinfluencer
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./accounts:/app/accounts
      - ./data:/app/data
      - ${USERPROFILE}/.android:/root/.android
    environment:
      - HOME=/root
      - ADB_SERVER_SOCKET=tcp:5037
      - NOCODB_BASE_URL=${NOCODB_BASE_URL}
      - NOCODB_TOKEN=${NOCODB_TOKEN}
      - NOCODB_PROJECT_ID=${NOCODB_PROJECT_ID}
      - NOCODB_HISTORY_FILTERS_TABLE_ID=${NOCODB_HISTORY_FILTERS_TABLE_ID}
      - NOCODB_HISTORY_FILTERS_VIEW_ID=${NOCODB_HISTORY_FILTERS_VIEW_ID}
      - NOCODB_INTERACTED_USERS_TABLE_ID=${NOCODB_INTERACTED_USERS_TABLE_ID}
      - NOCODB_INTERACTED_USERS_VIEW_ID=${NOCODB_INTERACTED_USERS_VIEW_ID}
      - PYTHONUNBUFFERED=1
      - TZ=UTC
    privileged: true
```

## API Endpoints

### Session Management
- `POST /start_session`: Start an automation session
  ```json
  {
    "account": "account_username"
  }
  ```
- `POST /stop_session`: Stop an automation session
  ```json
  {
    "account": "account_username"
  }
  ```
- `GET /session_status/{account}`: Get session status

### Configuration
- `GET /accounts`: List all configured accounts
- `GET /account_config/{account}`: Get account configuration
- `POST /account_config/{account}`: Update account configuration
- `GET /interaction_limits/{account}`: Get interaction limits

### Statistics
- `GET /bot_stats/{account}`: Get bot statistics
- `GET /health`: Container health check

## Account Configuration
Place account configurations in `/accounts/{username}/config.yml`:
```yaml
username: account_username
app_id: com.instagram.android
use_cloned_app: false
allow_untested_ig_version: false
screen_sleep: true
debug: true
use_nocodb: true
init_db: true
total_crashes_limit: 5
count_app_crashes: false
shuffle_jobs: true
truncate_sources: "2-5"
watch_video_time: "15-35"
watch_photo_time: "3-4"
delete_interacted_users: true
```

## Device Connection
1. Enable USB debugging on Android device
2. Connect device via ADB:
   ```bash
   adb connect <device_ip>:<port>
   ```
3. Verify connection:
   ```bash
   adb devices
   ```

## Health Monitoring
- Container includes built-in health check
- Monitors every 30 seconds
- Checks API endpoint: `http://localhost:8000/health`
- Returns:
  ```json
  {
    "status": "healthy",
    "timestamp": "2024-12-01T05:33:29.667798"
  }
  ```

## Logging
- API logs: `/app/logs/api.log`
- Account-specific logs: `/app/logs/{account}.log`
- NocoDB operation logs: `/app/logs/nocodb_operations.log`

## Security Notes
- Container runs in privileged mode for device access
- ADB keys are shared from host system
- Sensitive data should be provided via environment variables
- No hardcoded credentials in configurations

## Troubleshooting
1. ADB Connection Issues:
   ```bash
   # Restart ADB server
   adb kill-server
   adb start-server
   ```

2. API Access Issues:
   - Verify port mapping: `docker-compose ps`
   - Check logs: `docker-compose logs`

3. Permission Issues:
   - Ensure proper volume permissions
   - Verify ADB key access

## Build from Source
```bash
# Clone repository
git clone https://github.com/oculairmedia/virtualinfluencer.git

# Build image
docker-compose build

# Run container
docker-compose up -d
```
docker push oculair/virtualinfluencer:latest

to test use
curl -X POST http://localhost:8000/start_session -H Content-Type: application/json -d {"account": "quecreate"}

curl http://192.168.50.90:8000/session_status/quecreate