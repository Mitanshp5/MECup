"""
Authentication models - DISABLED for development.
Using simple classes instead of SQLAlchemy models.
"""

import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"

class User:
    """Simple user class without database dependency."""
    def __init__(self, username="admin", role=None, is_active=True):
        self.id = 1
        self.username = username
        self.hashed_password = "dummy"
        self.role = role or UserRole.ADMIN
        self.is_active = is_active
