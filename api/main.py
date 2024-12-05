import logging
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psutil
from api.services.session_service import SessionService
from api.services.account_service import AccountService
from api.routers import health, accounts, sessions

# Setup logging
def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # API Logger
    api_logger = logging.getLogger("api")
    api_logger.setLevel(logging.DEBUG)
    api_handler = logging.FileHandler(os.path.join(log_dir, "api.log"))
    api_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    api_logger.addHandler(api_handler)

    # Session Logger
    session_logger = logging.getLogger("session")
    session_logger.setLevel(logging.DEBUG)
    session_handler = logging.FileHandler(os.path.join(log_dir, "session.log"))
    session_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    session_logger.addHandler(session_handler)

    return api_logger, session_logger

app = FastAPI(title="Instagram Automation API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services and loggers
@app.on_event("startup")
async def startup_event():
    api_logger, session_logger = setup_logging()
    
    # Set base directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    accounts_dir = os.path.join(base_dir, "accounts")
    
    # Initialize services
    app.state.account_service = AccountService(accounts_dir)
    app.state.session_service = SessionService(accounts_dir, session_logger)
    
    # Add loggers to app state
    app.state.api_logger = api_logger
    app.state.session_logger = session_logger
    
    api_logger.info("API started successfully")

# Include routers
app.include_router(health.router)
app.include_router(accounts.router)
app.include_router(sessions.router)

# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        request.app.state.api_logger.error(f"Unhandled error: {str(e)}")
        raise

# Track active tasks
active_tasks = set()

# Track sync plugin
sync_plugin = None

# Track active sessions and their status
active_sessions: Dict[str, dict] = {}

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = 120

def register_task(task):
    """Register an active task"""
    active_tasks.add(task)
    task.add_done_callback(active_tasks.discard)

async def cleanup_tasks():
    """Cleanup all active tasks"""
    tasks = list(active_tasks)
    if not tasks:
        return
        
    app.state.api_logger.info(f"Cleaning up {len(tasks)} active tasks...")
    for task in tasks:
        if not task.done():
            task.cancel()
            
    # Wait for all tasks to complete with a timeout
    with suppress(asyncio.TimeoutError, asyncio.CancelledError):
        await asyncio.wait(tasks, timeout=5.0)

class SessionRequest(BaseModel):
    account: str

class SessionStatus(BaseModel):
    account: str
    status: str
    start_time: Optional[datetime]
    last_interaction: Optional[datetime]
    total_interactions: int = 0
    errors: Optional[str] = None
    process_info: Optional[dict] = None
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    uptime_minutes: Optional[float] = None
    is_responsive: bool = True

class BotStats(BaseModel):
    account: str
    total_interactions_24h: int = 0
    successful_interactions_24h: int = 0
    failed_interactions_24h: int = 0
    success_rate_24h: float = 0.0
    average_response_time_ms: float = 0.0
    uptime_hours: float = 0.0
    total_sessions: int = 0
    current_session_duration: Optional[float] = None
    memory_usage_trend: list = []
    cpu_usage_trend: list = []
    error_count_24h: int = 0

class InteractionLimits(BaseModel):
    """Model for interaction limits"""
    account: str
    likes_limit: int
    follow_limit: int
    unfollow_limit: int
    comments_limit: int
    pm_limit: int
    watch_limit: int
    success_limit: int
    total_limit: int
    scraped_limit: int
    crashes_limit: int
    time_delta_session: int

class AccountInfo(BaseModel):
    """Model for account information"""
    username: str
    total_posts: int = 0
    total_followers: int = 0
    total_following: int = 0
    last_session_time: Optional[datetime] = None
    is_active: bool = False
    config_exists: bool = True

class AccountConfig(BaseModel):
    """Model for account configuration"""
    username: str
    app_id: str = "com.instagram.android"
    use_cloned_app: bool = False
    allow_untested_ig_version: bool = False
    screen_sleep: bool = True
    screen_record: bool = False
    speed_multiplier: float = 1.0
    debug: bool = True
    close_apps: bool = False
    kill_atx_agent: bool = False
    restart_atx_agent: bool = False
    disable_block_detection: bool = False
    disable_filters: bool = False
    dont_type: bool = False
    use_nocodb: bool = True
    init_db: bool = True
    total_crashes_limit: int = 5
    count_app_crashes: bool = False
    shuffle_jobs: bool = True
    truncate_sources: str = "2-5"
    # Action configurations
    blogger_followers: list[str] = []
    watch_video_time: str = "15-35"
    watch_photo_time: str = "3-4"
    delete_interacted_users: bool = True
    # Optional fields
    device: Optional[str] = None
    scrape_to_file: Optional[str] = None
    can_reinteract_after: Optional[int] = None
    feed: Optional[str] = None
    unfollow: Optional[str] = None
    unfollow_any: Optional[str] = None
    unfollow_non_followers: Optional[str] = None

    class Config:
        alias_generator = lambda string: string.replace('_', '-')
        allow_population_by_field_name = True

class UpdateAccountConfig(BaseModel):
    """Model for account configuration updates"""
    config: Dict[str, Any]

class ConfigEntry(BaseModel):
    """Model for a single configuration entry"""
    key: str
    value: Any

class ArrayConfigEntry(BaseModel):
    """Model for array configuration entry"""
    key: str
    item: Any

async def check_session_timeout():
    """Background task to check for session timeouts"""
    while True:
        try:
            current_time = datetime.now()
            for account, session in active_sessions.items():
                if session['status'] != 'running':
                    continue
                
                # Check last interaction time
                last_interaction = session.get('last_interaction', session.get('start_time'))
                if last_interaction:
                    idle_time = current_time - last_interaction
                    if idle_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                        app.state.api_logger.warning(f"Session timeout for account {account} after {idle_time}")
                        # Stop the session
                        await stop_session(SessionRequest(account=account))
            
            # Check every minute
            await asyncio.sleep(60)
        except Exception as e:
            app.state.api_logger.error(f"Error in session timeout checker: {str(e)}")
            await asyncio.sleep(60)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup plugins and resources on shutdown"""
    await cleanup_tasks()
    app.state.api_logger.info("All tasks cleaned up.")

def get_process_info(pid: int) -> dict:
    """Get detailed process information"""
    try:
        process = psutil.Process(pid)
        with process.oneshot():
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=0.1)
            create_time = datetime.fromtimestamp(process.create_time())
            children = process.children(recursive=True)
            
            child_info = []
            total_child_memory = 0
            for child in children:
                try:
                    with child.oneshot():
                        child_memory = child.memory_info().rss / 1024 / 1024  # MB
                        total_child_memory += child_memory
                        child_info.append({
                            'pid': child.pid,
                            'memory_mb': round(child_memory, 2),
                            'cpu_percent': child.cpu_percent(interval=0.1)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'main_process': {
                    'pid': process.pid,
                    'memory_mb': round(memory_info.rss / 1024 / 1024, 2),  # Convert to MB
                    'cpu_percent': cpu_percent,
                    'create_time': create_time,
                    'status': process.status()
                },
                'child_processes': child_info,
                'total_memory_mb': round(memory_info.rss / 1024 / 1024 + total_child_memory, 2),
                'total_processes': len(children) + 1
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        app.state.api_logger.warning(f"Could not get process info for PID {pid}: {str(e)}")
        return None

def read_file_lines(file_path: str) -> list[str]:
    """Read file and return lines while preserving format"""
    with open(file_path, 'r') as f:
        return f.readlines()

def write_file_lines(file_path: str, lines: list[str]):
    """Write lines back to file"""
    with open(file_path, 'w') as f:
        f.writelines(lines)

def update_yaml_value_in_lines(lines: list[str], key: str, value: Any) -> list[str]:
    """Update a specific key's value in the YAML lines while preserving format"""
    new_lines = []
    key_found = False
    
    for line in lines:
        if line.strip().startswith(f"{key}:"):
            # Preserve any inline comments
            comment = ""
            if "#" in line:
                comment = " " + line.split("#", 1)[1].rstrip()
            
            # Format the value appropriately
            if isinstance(value, list):
                formatted_value = str(value).replace("'", '"')
            else:
                formatted_value = str(value)
            
            new_lines.append(f"{key}: {formatted_value}{comment}\n")
            key_found = True
        else:
            new_lines.append(line)
    
    if not key_found:
        # Add new key at the end of the appropriate section
        new_lines.append(f"{key}: {value}\n")
    
    return new_lines
