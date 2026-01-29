from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session # kept for type hinting
try:
    from auth import models, schemas
    from database import get_db
except ImportError:
    from . import models, schemas
    from ..database import get_db

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    # Ensure all values are JSON serializable (Enum -> str)
    for k, v in to_encode.items():
        if isinstance(v, enum.Enum):
            to_encode[k] = v.value
            
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

import enum 

# Dependency to get current user (BYPASS MODE)
async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    # BYPASS LOGIN: Return dummy admin user
    return models.User(username="admin", role=models.UserRole.ADMIN, is_active=True)

    # ORIGINAL SECURITY LOGIC (Commented out)
    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Could not validate credentials",
    #     headers={"WWW-Authenticate": "Bearer"},
    # )
    # try:
    #     payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    #     username: str = payload.get("sub")
    #     role_str: str = payload.get("role")
    #     if username is None:
    #         raise credentials_exception
    #     token_data = schemas.TokenData(username=username, role=models.UserRole(role_str) if role_str else None)
    # except JWTError:
    #     raise credentials_exception
    
    # # Async query
    # from sqlalchemy import select
    # result = await db.execute(select(models.User).filter(models.User.username == token_data.username))
    # user = result.scalars().first()
    
    # if user is None:
    #     raise credentials_exception
    # return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Role Checkers
def require_admin(user: models.User = Depends(get_current_active_user)):
    if user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

def require_operator(user: models.User = Depends(get_current_active_user)):
    if user.role not in [models.UserRole.ADMIN, models.UserRole.OPERATOR]:
        raise HTTPException(status_code=403, detail="Operator privileges required")
    return user
