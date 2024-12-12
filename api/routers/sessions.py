from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from api.models import SessionRequest, SessionStatus
from typing import Optional

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={404: {"description": "Session not found"}}
)

@router.post("/start")
async def start_session(session_request: SessionRequest, request: Request):
    """
    Start a new bot session for the specified account.
    """
    try:
        return await request.app.state.session_service.start_session(session_request)
    except Exception as e:
        request.app.state.api_logger.error(f"Error starting session: {str(e)}")
        raise

@router.post("/stop")
async def stop_session(session_request: SessionRequest, request: Request):
    """
    Stop an active bot session.
    """
    try:
        return await request.app.state.session_service.stop_session(session_request)
    except Exception as e:
        request.app.state.api_logger.error(f"Error stopping session: {str(e)}")
        raise

@router.get("/{account}/status", response_model=Optional[SessionStatus])
async def get_session_status(account: str, request: Request):
    """
    Get the current status of a bot session.
    """
    try:
        return await request.app.state.session_service.get_session_status(account)
    except Exception as e:
        request.app.state.api_logger.error(f"Error getting session status: {str(e)}")
        raise

@router.get("/{account}/logs")
async def stream_session_logs(account: str, request: Request):
    """
    Stream logs for a specific account in real-time using Server-Sent Events (SSE).
    
    The endpoint returns a stream of log entries in the following format:
    ```
    data: {
        "timestamp": "12/12 12:24:32",
        "message": "Bot is updated.",
        "level": "INFO"
    }
    ```
    
    Each log entry is separated by two newlines as per SSE specification.
    """
    try:
        return StreamingResponse(
            request.app.state.session_service.stream_logs(account),
            media_type="text/event-stream"
        )
    except Exception as e:
        request.app.state.api_logger.error(f"Error streaming logs: {str(e)}")
        raise
