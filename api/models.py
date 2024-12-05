from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class SessionRequest(BaseModel):
    account: str
    config: Optional[Dict[str, Any]] = None

class SessionStatus(BaseModel):
    account: str
    status: str
    start_time: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    total_interactions: int = 0
    errors: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    is_responsive: bool = False

class AccountConfig(BaseModel):
    username: str
    device: str
    working_hours: Optional[Dict[str, list[str]]] = None
    actions: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    plugins: Optional[list[str]] = None
    proxy: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class AccountInfo(BaseModel):
    name: str
    config: Optional[AccountConfig] = None
    status: Optional[str] = None
    last_run: Optional[datetime] = None
    total_interactions: int = 0
    errors: Optional[str] = None
