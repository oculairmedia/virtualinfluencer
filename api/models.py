from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class SessionRequest(BaseModel):
    account: str

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
    app_id: Optional[str] = None
    hashtag_posts_recent: Optional[list[str]] = None
    blogger_followers: Optional[list[str]] = None
    working_hours: Optional[list[str]] = None
    feed: Optional[str] = None
    watch_video_time: Optional[str] = None
    watch_photo_time: Optional[str] = None
    delete_interacted_users: Optional[bool] = None
    comment_percentage: Optional[str] = None
    pm_percentage: Optional[str] = None
    delete_removed_followers: Optional[bool] = None
    analytics: Optional[bool] = None
    telegram_reports: Optional[bool] = None
    interactions_count: Optional[str] = None
    likes_count: Optional[str] = None
    likes_percentage: Optional[str] = None
    total_likes_limit: Optional[str] = None
    total_follows_limit: Optional[str] = None
    total_unfollows_limit: Optional[int] = None
    time_delta: Optional[str] = None
    repeat: Optional[str] = None
    total_sessions: Optional[int] = None

    class Config:
        allow_population_by_field_name = True

class ConfigUpdate(BaseModel):
    hashtag_posts_recent: Optional[list[str]] = None
    blogger_followers: Optional[list[str]] = None
    working_hours: Optional[list[str]] = None
    class Config:
        allow_population_by_field_name = True

class AccountInfo(BaseModel):
    name: str
    config: Optional[AccountConfig] = None
    status: Optional[str] = None
    last_run: Optional[datetime] = None
    total_interactions: int = 0
    errors: Optional[str] = None
