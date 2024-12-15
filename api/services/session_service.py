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
import sys

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
            # Use Docker container paths
            base_dir = "/app"  # Fixed path in Docker container
            config_path = os.path.join(base_dir, "accounts", account, "config.yml")
            run_script = os.path.join(base_dir, "run.py")
            
            self.logger.info(f"Starting session for account {account} with config {config_path}")
            
            if not os.path.exists(config_path):
                error_msg = f"Configuration not found for account: {account} at path: {config_path}"
                self.logger.error(error_msg)
                raise HTTPException(status_code=404, detail=error_msg)
                
            # Create a background task to run the bot
            cmd = ["python3", run_script, "--config", config_path, "--use-nocodb", "--debug"]
            self.logger.info(f"Running command: {' '.join(cmd)}")
            self.logger.info(f"Working directory: {base_dir}")
            
            # Set up environment variables
            env = os.environ.copy()
            env["PYTHONPATH"] = base_dir
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                cwd=base_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait a short time for initial output
            await asyncio.sleep(2)
            
            # Read any initial output
            stdout_data, stderr_data = process.communicate(timeout=1)
            
            # Check if the output contains only the config file timestamp message
            if stderr_data and "has been saved last time at" in stderr_data:
                # This is just an informational message, not an error
                self.logger.info(f"Config file info for {account}: {stderr_data.strip()}")
                
                # Start a new process since communicate() closed the previous one
                process = subprocess.Popen(
                    cmd,
                    cwd=base_dir,
                    env=env,
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
                    "process": process,
                    "status": "running"
                }

                # Start background task to monitor process output
                asyncio.create_task(self._monitor_process_output(account, process))
                
                return {"status": "started", "account": account}
            else:
                # Real error occurred
                error_msg = stderr_data.strip() if stderr_data else "Unknown error occurred"
                raise Exception(f"Process failed to start: {error_msg}")

        except subprocess.TimeoutExpired:
            # Process is still running, which is good
            self.active_sessions[account] = {
                "pid": process.pid,
                "start_time": datetime.now(),
                "last_interaction": datetime.now(),
                "total_interactions": 0,
                "process": process,
                "status": "running"
            }
            
            # Start background task to monitor process output
            asyncio.create_task(self._monitor_process_output(account, process))
            
            return {"status": "started", "account": account}
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to start session for {account}: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Failed to start session: {error_msg}")

    async def _monitor_process_output(self, account: str, process: subprocess.Popen):
        """Monitor process output in a background task"""
        try:
            while True:
                if process.poll() is not None:
                    # Process has ended
                    break

                # Read output (non-blocking)
                stdout_line = process.stdout.readline() if process.stdout else ""
                stderr_line = process.stderr.readline() if process.stderr else ""

                if stdout_line:
                    self.logger.info(f"[{account}] {stdout_line.strip()}")
                if stderr_line:
                    if "has been saved last time at" in stderr_line:
                        self.logger.info(f"[{account}] {stderr_line.strip()}")
                    else:
                        self.logger.error(f"[{account}] {stderr_line.strip()}")

                await asyncio.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Error monitoring process output for {account}: {str(e)}")
        finally:
            # Clean up session if process has ended
            if account in self.active_sessions:
                del self.active_sessions[account]

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
                # Try to terminate the main process and its children
                try:
                    parent = psutil.Process(process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        child.terminate()
                    parent.terminate()
                    
                    # Wait for processes to terminate
                    gone, alive = psutil.wait_procs([parent] + children, timeout=3)
                    
                    # Force kill if still alive
                    for p in alive:
                        p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
                    self.logger.warning(f"Process termination warning for {account}: {str(e)}")

            session_info = self.active_sessions.pop(account)
            self.logger.info(f"Stopped session for account {account}")
            return {"status": "success", "message": f"Session stopped for account {account}"}
        except Exception as e:
            self.logger.error(f"Failed to stop session for {account}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to stop session: {str(e)}")

    async def get_session_status(self, account: str) -> Optional[SessionStatus]:
        """Get the current status of a bot session"""
        if account not in self.active_sessions:
            return SessionStatus(
                account=account,
                status="inactive",
                start_time=None,
                last_interaction=None,
                total_interactions=0,
                is_responsive=False
            )

        session = self.active_sessions[account]
        process = session.get("process")
        is_responsive = False
        memory_usage_mb = None
        cpu_percent = None
        uptime_minutes = None

        if process:
            try:
                # Check if process is still running
                if process.poll() is None:
                    psutil_proc = psutil.Process(process.pid)
                    with psutil_proc.oneshot():
                        memory_usage_mb = psutil_proc.memory_info().rss / 1024 / 1024
                        cpu_percent = psutil_proc.cpu_percent()
                        if session.get("start_time"):
                            uptime_minutes = (datetime.now() - session["start_time"]).total_seconds() / 60
                        is_responsive = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return SessionStatus(
            account=account,
            status=session.get("status", "unknown"),
            start_time=session.get("start_time"),
            last_interaction=session.get("last_interaction"),
            total_interactions=session.get("total_interactions", 0),
            errors=session.get("errors"),
            memory_usage_mb=round(memory_usage_mb, 2) if memory_usage_mb else None,
            cpu_percent=round(cpu_percent, 2) if cpu_percent else None,
            uptime_minutes=round(uptime_minutes, 2) if uptime_minutes else None,
            is_responsive=is_responsive
        )

    async def stream_logs(self, account: str) -> AsyncGenerator[str, None]:
        """Stream logs for a specific account in real-time"""
        log_file = os.path.join("/app/logs", f"{account}.log")
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
