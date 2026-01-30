"""
Authentication router - DISABLED for development.
All endpoints return dummy responses.
"""

from fastapi import APIRouter
try:
    from auth import models, schemas
except ImportError:
    from . import models, schemas

router = APIRouter(tags=["Authentication"])

# Mock users for display
MOCK_USERS = [
    {"id": 1, "username": "admin", "role": models.UserRole.ADMIN, "is_active": True},
    {"id": 2, "username": "operator", "role": models.UserRole.OPERATOR, "is_active": True},
    {"id": 3, "username": "viewer", "role": models.UserRole.VIEWER, "is_active": True},
]

@router.post("/token")
async def login_for_access_token():
    """Bypass login - always returns a valid token."""
    return {"access_token": "bypass_token", "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me():
    """Return dummy admin user."""
    return {"id": 1, "username": "admin", "role": "ADMIN", "is_active": True}

@router.get("/users")
async def list_users():
    """Return mock users list."""
    return MOCK_USERS

@router.post("/users")
async def create_user(user_in: schemas.UserCreate):
    """Mock user creation - just returns the input."""
    return {
        "id": len(MOCK_USERS) + 1,
        "username": user_in.username,
        "role": user_in.role,
        "is_active": True
    }
