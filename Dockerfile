FROM oculair/virtualinfluencer:working_backup

# Install FastAPI and dependencies
RUN pip install --no-cache-dir \
    fastapi==0.115.5 \
    uvicorn==0.32.1 \
    pydantic==2.10.2 \
    PyYAML==6.0.1

# Create API directory and files
WORKDIR /app

# Create API directory
RUN mkdir -p /app/api

# Create FastAPI main.py
RUN echo '\
from fastapi import FastAPI, HTTPException\n\
from pydantic import BaseModel\n\
import os\n\
import subprocess\n\
import yaml\n\
import datetime\n\
import json\n\
from typing import Optional, Dict, Any\n\
\n\
app = FastAPI()\n\
\n\
class SessionRequest(BaseModel):\n\
    account: str\n\
    config: Optional[Dict[str, Any]] = None\n\
\n\
@app.get("/health")\n\
async def health_check():\n\
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}\n\
\n\
@app.post("/start_session")\n\
async def start_session(request: SessionRequest):\n\
    try:\n\
        account_dir = f"/app/accounts/{request.account}"\n\
        if not os.path.exists(account_dir):\n\
            os.makedirs(account_dir)\n\
\n\
        # Update config if provided\n\
        if request.config:\n\
            config_file = f"{account_dir}/config.yml"\n\
            with open(config_file, "w") as f:\n\
                yaml.dump(request.config, f)\n\
\n\
        # Start GramAddict session\n\
        cmd = ["python", "-m", "gramaddict", "--config", account_dir]\n\
        process = subprocess.Popen(cmd)\n\
\n\
        return {"message": f"Started session for {request.account}", "pid": process.pid}\n\
    except Exception as e:\n\
        raise HTTPException(status_code=500, detail=str(e))\n\
\n\
@app.post("/stop_session")\n\
async def stop_session(request: SessionRequest):\n\
    try:\n\
        # Find and kill GramAddict process for this account\n\
        cmd = f"pkill -f \"gramaddict --config /app/accounts/{request.account}\""\n\
        subprocess.run(cmd, shell=True)\n\
        return {"message": f"Stopped session for {request.account}"}\n\
    except Exception as e:\n\
        raise HTTPException(status_code=500, detail=str(e))\n\
\n\
@app.get("/session_status/{account}")\n\
async def get_session_status(account: str):\n\
    try:\n\
        # Check if process is running\n\
        cmd = f"pgrep -f \"gramaddict --config /app/accounts/{account}\""\n\
        result = subprocess.run(cmd, shell=True, capture_output=True)\n\
        \n\
        status = "running" if result.returncode == 0 else "stopped"\n\
        \n\
        # Get session start time from logs if available\n\
        log_file = f"/app/logs/{account}.log"\n\
        start_time = None\n\
        duration = "0:00:00"\n\
        \n\
        if os.path.exists(log_file):\n\
            with open(log_file, "r") as f:\n\
                for line in f:\n\
                    if "Session started" in line:\n\
                        start_time = line.split("[")[1].split("]")[0]\n\
                        break\n\
        \n\
        return {\n\
            "status": status,\n\
            "start_time": start_time,\n\
            "duration": duration\n\
        }\n\
    except Exception as e:\n\
        raise HTTPException(status_code=500, detail=str(e))\n\
\n\
@app.get("/accounts")\n\
async def list_accounts():\n\
    try:\n\
        accounts = []\n\
        accounts_dir = "/app/accounts"\n\
        if os.path.exists(accounts_dir):\n\
            for account in os.listdir(accounts_dir):\n\
                account_path = os.path.join(accounts_dir, account)\n\
                if os.path.isdir(account_path):\n\
                    # Get config if available\n\
                    config = {}\n\
                    config_file = os.path.join(account_path, "config.yml")\n\
                    if os.path.exists(config_file):\n\
                        with open(config_file, "r") as f:\n\
                            config = yaml.safe_load(f)\n\
                    \n\
                    accounts.append({\n\
                        "name": account,\n\
                        "config": config\n\
                    })\n\
        return {"accounts": accounts}\n\
    except Exception as e:\n\
        raise HTTPException(status_code=500, detail=str(e))\n\
' > /app/api/main.py

# Start script to handle ADB and FastAPI
RUN echo '\
#!/bin/bash\n\
\n\
# Start ADB server\n\
adb start-server\n\
\n\
# Wait for ADB to start\n\
sleep 5\n\
\n\
# Connect to device if IP is provided\n\
if [ ! -z "$ADB_DEVICE_IP" ] && [ ! -z "$ADB_DEVICE_PORT" ]; then\n\
    echo "Connecting to device at $ADB_DEVICE_IP:$ADB_DEVICE_PORT"\n\
    adb connect $ADB_DEVICE_IP:$ADB_DEVICE_PORT\n\
fi\n\
\n\
# Start FastAPI server\n\
cd /app/api && uvicorn main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 8000 5037

CMD ["/app/start.sh"]
