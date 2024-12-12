import os
import logging
import asyncio
import psutil
import subprocess
from datetime import datetime
from typing import Optional, Dict, AsyncGenerator
from api.models import SessionStatus, SessionRequest
from fastapi import HTTPException
import aiofiles
import re
from datetime import datetime

class SessionService:
    def __init__(self, accounts_dir: str, logger: logging.Logger):
        self.accounts_dir = accounts_dir
        self.logger = logger
        self.active_sessions: Dict[str, Dict] = {}

    async def start_session(self, session_request: SessionRequest) -> Dict:
        """Start a new bot session for the specified account"""
        account = session_request.account
        if account in self.active_sessions:
            self.logger.warning(f"Session already exists for account {account}")
            return {"message": f"Session already running for {account}", "pid": self.active_sessions[account].get("pid")}

        try:
            # Start the GramAddict bot process
            config_path = os.path.join(self.accounts_dir, account, "config.yml")
            if not os.path.exists(config_path):
                raise HTTPException(status_code=404, detail=f"Config not found for account {account}")

            # Build the command to run GramAddict
            cmd = [
                "python", "-m", "GramAddict",
                "--config", config_path,
                "--use-nocodb"  # Add other arguments as needed
            ]

            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Store session info
            self.active_sessions[account] = {
                "pid": process.pid,
                "start_time": datetime.now(),
                "last_interaction": datetime.now(),
                "total_interactions": 0,
                "process": process
            }

            self.logger.info(f"Started session for account {account} with PID {process.pid}")
            return {"message": f"Started session for {account}", "pid": process.pid}
        except Exception as e:
            self.logger.error(f"Failed to start session for {account}: {str(e)}")
            raise

    async def stop_session(self, session_request: SessionRequest) -> Dict:
        """Stop an active bot session"""
        account = session_request.account
        if account not in self.active_sessions:
            self.logger.warning(f"No active session found for account {account}")
            return {"message": f"No active session for {account}"}

        try:
            session_info = self.active_sessions[account]
            process = session_info.get("process")
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

            session_info = self.active_sessions.pop(account)
            self.logger.info(f"Stopped session for account {account}")
            return {"message": f"Stopped session for {account}", "uptime_minutes": 0}
        except Exception as e:
            self.logger.error(f"Failed to stop session for {account}: {str(e)}")
            raise

    async def get_session_status(self, account: str) -> Optional[SessionStatus]:
        """Get the current status of a bot session"""
        if account not in self.active_sessions:
            return None

        session = self.active_sessions[account]
        process = session.get("process")
        is_responsive = False
        memory_usage_mb = 0.0
        cpu_percent = 0.0

        if process:
            try:
                # Check if process is still running
                if process.poll() is None:
                    psutil_proc = psutil.Process(process.pid)
                    memory_usage_mb = psutil_proc.memory_info().rss / 1024 / 1024
                    cpu_percent = psutil_proc.cpu_percent()
                    is_responsive = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return SessionStatus(
            account=account,
            status="running" if is_responsive else "not_responding",
            start_time=session["start_time"],
            last_interaction=session["last_interaction"],
            total_interactions=session["total_interactions"],
            memory_usage_mb=memory_usage_mb,
            cpu_percent=cpu_percent,
            is_responsive=is_responsive
        )

    async def stream_logs(self, account: str) -> AsyncGenerator[str, None]:
        """Stream logs for a specific account in real-time"""
        log_file = os.path.join("logs", f"{account}.log")
        if not os.path.exists(log_file):
            raise HTTPException(status_code=404, detail=f"No log file found for account {account}")

        # Keep track of the last position we read from
        last_position = 0
        
        try:
            while True:
                async with aiofiles.open(log_file, mode='r', encoding='utf-8', errors='ignore') as file:
                    # Seek to the last position we read from
                    await file.seek(last_position)
                    
                    # Read any new content
                    content = await file.read()
                    
                    if content:
                        # Update the last position
                        last_position += len(content.encode('utf-8'))
                        
                        # Parse and format log entries
                        for line in content.splitlines():
                            if line.strip():
                                # Extract timestamp and format entry
                                timestamp_match = re.match(r'\[(.*?)\]', line)
                                if timestamp_match:
                                    timestamp = timestamp_match.group(1)
                                    message = line[line.find(']')+1:].strip()
                                    log_entry = {
                                        "timestamp": timestamp,
                                        "message": message,
                                        "level": self._extract_log_level(line)
                                    }
                                    yield f"data: {str(log_entry)}\n\n"
                    
                    # Wait a bit before checking for new content
                    await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(f"Error streaming logs for {account}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _extract_log_level(self, log_line: str) -> str:
        """Extract log level from a log line"""
        level_match = re.search(r'\]\s+(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+\|', log_line)
        return level_match.group(1) if level_match else "INFO"
