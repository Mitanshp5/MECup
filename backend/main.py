import sys
import os
import logging
from contextlib import asynccontextmanager

# Reduce logging verbosity
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy.orm import Session

# Database & Auth
from database import engine, get_db
from auth import models as auth_models, router as auth_router, security as auth_security

# Create Tables
auth_models.Base.metadata.create_all(bind=engine)

# from production_rag.fastapi_server import router as rag_router, lifespan as rag_lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    # async with rag_lifespan(app):
    #     yield
    # Create Default Admin User
    try:
        db = next(get_db())
        # Check for 'mee' user
        user = db.query(auth_models.User).filter(auth_models.User.username == "mee").first()
        
        # Calculate expected hash for empty password
        hashed_pwd = auth_security.get_password_hash("")
        
        if not user:
            print("[Backend] Creating default user 'mee'...", flush=True)
            new_user = auth_models.User(
                username="mee",
                hashed_password=hashed_pwd,
                role="admin"
            )
            db.add(new_user)
            db.commit()
            print("[Backend] Default user created: mee / (empty)", flush=True)
        else:
            # Force update password to ensure it matches current security scheme
            user.hashed_password = hashed_pwd
            # Ensure role is admin
            user.role = "admin"
            db.commit()
            print("[Backend] User 'mee' password reset to empty (sync with security scheme).", flush=True)
    except Exception as e:
        print(f"[Backend] Failed to ensure admin user: {e}", flush=True)

    try:
        from inference.inference_service import get_predictor
        print("[Backend] Initializing Inference Engine...", flush=True)
        get_predictor()
    except Exception as e:
        print(f"[Backend] Failed to initialize inference: {e}", flush=True)

    # Initialize PLC System (Polling) - Main Process Only
    try:
        from plc.endpoints import init_plc_system
        init_plc_system()
    except Exception as e:
        print(f"[Backend] Failed to initialize PLC: {e}", flush=True)

    yield

app = FastAPI(
    title="Unified Backend API",
    description="Combined API for MECup application",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS globally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router.router)
from plc.endpoints import router as plc_router
app.include_router(plc_router, tags=["PLC"])

try:
    from camera.endpoints import router as camera_router
    app.include_router(camera_router, tags=["Camera"])
except Exception:
    pass

try:
    from inference.endpoints import router as inference_router
    app.include_router(inference_router, tags=["Inference"])
except Exception:
    pass

try:
    app.include_router(rag_router, tags=["RAG"])
    
except Exception:
    pass

@app.get("/")
async def root():
    return {"message": "MECup Backend is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    print("[Backend] Starting MECup Backend on port 5001...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="warning", access_log=False)
