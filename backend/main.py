import sys
import os
import logging
from contextlib import asynccontextmanager

# Reduce logging verbosity
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
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

@app.get("/")
async def root():
    return {"message": "MECup Backend is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    print("[Backend] Starting MECup Backend on port 5001...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="warning", access_log=False)
