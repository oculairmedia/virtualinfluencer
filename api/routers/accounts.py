from fastapi import APIRouter, Request, HTTPException
from api.models import AccountConfig, AccountInfo

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
