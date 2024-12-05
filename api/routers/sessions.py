from fastapi import APIRouter, Request, HTTPException
from api.models import SessionRequest, SessionStatus

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={404: {"description": "Session not found"}}
)

@router.post("/start_session")
async def start_session(session_request: SessionRequest, request: Request):
    """
    Start a new Instagram bot session for the specified account.
    """
    try:
        result = await request.app.state.session_service.start_session(session_request)
        request.app.state.session_logger.info(f"Started session for account {session_request.account}")
        return result
    except Exception as e:
        request.app.state.session_logger.error(f"Error starting session for account {session_request.account}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop_session")
async def stop_session(session_request: SessionRequest, request: Request):
    """
    Stop an active Instagram bot session for the specified account.
    """
    try:
        result = await request.app.state.session_service.stop_session(session_request)
        request.app.state.session_logger.info(f"Stopped session for account {session_request.account}")
        return result
    except Exception as e:
        request.app.state.session_logger.error(f"Error stopping session for account {session_request.account}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{account}", response_model=SessionStatus)
async def get_session_status(account: str, request: Request):
    """
    Get the current status of an Instagram bot session for the specified account.
    """
    try:
        status = await request.app.state.session_service.get_session_status(account)
        if not status:
            raise HTTPException(status_code=404, detail=f"Session not found for account {account}")
        request.app.state.session_logger.debug(f"Retrieved status for account {account}: {status.status}")
        return status
    except HTTPException:
        raise
    except Exception as e:
        request.app.state.session_logger.error(f"Error getting session status for account {account}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
