from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List, Any, Dict, Optional, Union
from api.models import AccountConfig, AccountInfo

class ConfigUpdate(BaseModel):
    """Model for configuration updates"""
    hashtag_posts_recent: Optional[list[str]] = None
    blogger_followers: Optional[list[str]] = None
    working_hours: Optional[list[str]] = None
    speed_multiplier: Optional[float] = None
    device: Optional[str] = None
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
    stories_count: Optional[str] = None
    stories_percentage: Optional[str] = None
    carousel_count: Optional[str] = None
    carousel_percentage: Optional[str] = None
    interact_percentage: Optional[str] = None
    follow_percentage: Optional[str] = None
    follow_limit: Optional[int] = None
    skipped_list_limit: Optional[str] = None
    skipped_posts_limit: Optional[int] = None
    fling_when_skipped: Optional[int] = None
    min_following: Optional[int] = None
    max_comments_pro_user: Optional[int] = None
    total_likes_limit: Optional[str] = None
    total_follows_limit: Optional[str] = None
    total_unfollows_limit: Optional[int] = None
    total_watches_limit: Optional[str] = None
    total_successful_interactions_limit: Optional[str] = None
    total_interactions_limit: Optional[str] = None
    total_comments_limit: Optional[str] = None
    total_pm_limit: Optional[str] = None
    total_scraped_limit: Optional[str] = None
    end_if_likes_limit_reached: Optional[bool] = None
    end_if_follows_limit_reached: Optional[bool] = None
    end_if_watches_limit_reached: Optional[bool] = None
    end_if_comments_limit_reached: Optional[bool] = None
    end_if_pm_limit_reached: Optional[bool] = None
    time_delta: Optional[str] = None
    repeat: Optional[str] = None
    total_sessions: Optional[int] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    responses={404: {"description": "Account not found"}}
)

@router.get("/", response_model=list[AccountInfo])
async def list_accounts(request: Request):
    """
    List all configured Instagram accounts.
    """
    try:
        return await request.app.state.account_service.list_accounts()
    except Exception as e:
        request.app.state.api_logger.error(f"Error listing accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{account}/config", response_model=AccountConfig)
async def get_account_config(account: str, request: Request):
    """
    Get configuration for a specific Instagram account.
    """
    try:
        config = await request.app.state.account_service.get_account_config(account)
        if not config:
            raise HTTPException(status_code=404, detail=f"Account {account} not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        request.app.state.api_logger.error(f"Error getting config for account {account}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{account}/config")
async def update_account_config(account: str, config: AccountConfig, request: Request):
    """
    Update configuration for a specific Instagram account.
    """
    try:
        return await request.app.state.account_service.update_account_config(account, config)
    except Exception as e:
        request.app.state.api_logger.error(f"Error updating config for account {account}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{account}/config")
async def patch_account_config(
    account: str,
    updates: ConfigUpdate,
    request: Request
):
    """
    Partially update configuration for a specific Instagram account.
    Allows updating specific fields like blogger-followers, hashtag-post-recent, device ID, and limits/schedules.
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        updates_dict = {}
        model_dict = updates.dict(exclude_none=True)
        
        # Process each field
        for field_name, field_value in model_dict.items():
            # Convert field name from snake_case to kebab-case
            yaml_key = field_name.replace('_', '-')
            
            # Handle list values
            if isinstance(field_value, list):
                # Convert all list items to strings
                updates_dict[yaml_key] = [str(item) for item in field_value]
            else:
                updates_dict[yaml_key] = field_value
                    
        # Update the configuration
        return await request.app.state.account_service.patch_account_config(account, updates_dict)
    except Exception as e:
        request.app.state.api_logger.error(f"Error patching config for account {account}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
