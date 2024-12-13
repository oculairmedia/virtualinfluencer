"""
Router package initialization
"""
from api.routers.health import router as health
from api.routers.accounts import router as accounts
from api.routers.sessions import router as sessions

__all__ = ["health", "accounts", "sessions"]
