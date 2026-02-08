from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

try:
    from ..database import get_db
except ImportError:
    from database import get_db
from . import models, schemas, security, dependencies

router = APIRouter(tags=["Authentication"])

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    username: str = Form(...),
    password: str = Form(""), 
    db: Session = Depends(get_db)
):
    # Construct a form_data like object to keep compatible variable names if desired, 
    # or just use username/password directly.
    class FormData:
        def __init__(self, u, p):
            self.username = u
            self.password = p
    form_data = FormData(username, password)
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    print(f"[AUTH DEBUG] Login attempt for: {form_data.username}", flush=True)
    if not user:
        print("[AUTH DEBUG] User not found", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    print(f"[AUTH DEBUG] User found. Verifying password...", flush=True)
    # print(f"[AUTH DEBUG] Hashed: {user.hashed_password}", flush=True) # Security risk in prod, ok for debug
    
    is_valid = security.verify_password(form_data.password, user.hashed_password)
    print(f"[AUTH DEBUG] Verify result: {is_valid}", flush=True)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Include role in the JWT payload/response logic if needed, but here we embed it in response
    access_token = security.create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@router.post("/users", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(dependencies.get_admin_user)
):
    """Create new user (Admin only)."""
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(
        username=user.username, 
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/users", response_model=List[schemas.UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(dependencies.get_admin_user)
):
    """List all users (Admin only)."""
    print(f"[AUTH DEBUG] Listing users. Current user: {current_user.username} ({current_user.role})", flush=True)
    users = db.query(models.User).offset(skip).limit(limit).all()
    print(f"[AUTH DEBUG] Found {len(users)} users", flush=True)
    return users

@router.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(dependencies.get_current_active_user)):
    return current_user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_admin_user)
):
    """Delete a user (Admin only)."""
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if user_to_delete.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Prevent deleting the last admin
    if user_to_delete.role == "admin":
        admin_count = db.query(models.User).filter(models.User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin user")
    
    db.delete(user_to_delete)
    db.commit()
    
    return {"success": True, "message": f"User {user_to_delete.username} deleted successfully"}
