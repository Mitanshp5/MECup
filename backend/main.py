import sys
import os
from contextlib import asynccontextmanager

# Add production_rag to python path so imports within it work
# Assuming main.py is in backend/ and production_rag is in backend/production_rag
# sys.path.append(os.path.join(os.path.dirname(__file__), 'production_rag'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# from production_rag.fastapi_server import router as rag_router, lifespan as rag_lifespan

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
# app.include_router(rag_router, tags=["RAG"])

from plc.endpoints import router as plc_router
app.include_router(plc_router, tags=["PLC"])

try:
    from camera.endpoints import router as camera_router
    app.include_router(camera_router, tags=["Camera"])
    print("[Backend] Camera module loaded successfully")
except Exception as e:
    print(f"[Backend] Camera module not available: {e}")
    print("[Backend] Continuing without camera support...")

@app.get("/")
async def root():
    return {"message": "MECup Backend is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Unified Backend API Server")
    print("=" * 60)
    # Use the same port as before or a new one? User didn't specify, but 5000 was used.
    uvicorn.run(app, host="0.0.0.0", port=5001)
