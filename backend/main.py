import sys
import os
from contextlib import asynccontextmanager

# Add production_rag to python path so imports within it work
# Assuming main.py is in backend/ and production_rag is in backend/production_rag
sys.path.append(os.path.join(os.path.dirname(__file__), 'production_rag'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the router or app from the module. 
# We'll need to refactor fastapi_server.py to export a router or we can mount its app.
# For better structure, let's refactor fastapi_server.py to export a router.
from production_rag.fastapi_server import router as rag_router, lifespan as rag_lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Call the RAG lifespan
    async with rag_lifespan(app):
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
app.include_router(rag_router, tags=["RAG"])

from plc.endpoints import router as plc_router
app.include_router(plc_router, tags=["PLC"])

@app.get("/")
async def root():
    return {"message": "MECup Backend is running"}

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Unified Backend API Server")
    print("=" * 60)
    # Use the same port as before or a new one? User didn't specify, but 5000 was used.
    uvicorn.run(app, host="0.0.0.0", port=5001)
