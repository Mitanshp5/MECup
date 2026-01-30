"""
Authentication security module - DISABLED for development.
All authentication is bypassed, returning a dummy admin user.
"""

# Dummy User class for compatibility
class DummyUser:
    def __init__(self):
        self.username = "admin"
        self.role = "admin"
        self.is_active = True

# Bypass function - always returns dummy user
async def get_current_user():
    return DummyUser()

async def get_current_active_user():
    return DummyUser()

def require_admin():
    return DummyUser()

def require_operator():
    return DummyUser()

# Dummy password functions
def verify_password(plain_password, hashed_password):
    return True

def get_password_hash(password):
    return "dummy_hash"

def create_access_token(data: dict, expires_delta=None):
    return "dummy_token"
