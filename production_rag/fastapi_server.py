"""
FastAPI Server for Production RAG Agent
Provides REST API endpoint for troubleshooting queries
"""

import sys
import os
from contextlib import asynccontextmanager

# Add script directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from agent import get_agent

# Global agent instance
agent = None

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

class HealthResponse(BaseModel):
    status: str
    agent_loaded: bool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup"""
    global agent
    print("[*] Initializing RAG agent...")
    agent = get_agent()
    print("[OK] Agent ready!")
    yield
    print("[*] Shutting down...")

app = FastAPI(
    title="Troubleshooting Agent API",
    description="RAG-powered troubleshooting for paint defect detection machines",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/troubleshoot", response_model=QueryResponse)
async def troubleshoot(request: QueryRequest):
    """Process a troubleshooting query"""
    global agent
    
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        print(f"[Query] {request.query}")
        response = agent.query(request.query)
        print(f"[Response] {response[:100]}...")
        return QueryResponse(response=response)
    except Exception as e:
        print(f"[Error] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        agent_loaded=agent is not None
    )

def main():
    print("=" * 60)
    print("Starting Troubleshooting Agent API Server (FastAPI)")
    print("=" * 60)
    print("Server will run on: http://localhost:5000")
    print("API endpoint: POST /api/troubleshoot")
    print("Health check: GET /api/health")
    print("Docs: http://localhost:5000/docs")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="warning")

if __name__ == "__main__":
    main()
