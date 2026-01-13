"""
FastAPI Server for Production RAG Agent
Provides REST API endpoint for troubleshooting queries
"""

import sys
import os
from contextlib import asynccontextmanager

# Add script directory to path if run directly (though now it's a module)
# sys.path.append('./production_rag') 

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

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
async def lifespan(app):
    """Initialize agent on startup"""
    global agent
    print("[*] Initializing RAG agent...")
    try:
        agent = get_agent()
        print("[OK] Agent ready!")
    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
    yield
    print("[*] Shutting down...")

# Create a router instead of an app
router = APIRouter()

@router.post("/api/troubleshoot", response_model=QueryResponse)
async def troubleshoot(request: QueryRequest):
    """Process a troubleshooting query"""
    global agent
    
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    if agent is None:
        # Try to initialize again or fail
        msg = "Agent not initialized"
        print(f"[Error] {msg}")
        raise HTTPException(status_code=503, detail=msg)
    
    try:
        print(f"[Query] {request.query}")
        response = agent.query(request.query)
        print(f"[Response] {response[:100]}...")
        return QueryResponse(response=response)
    except Exception as e:
        print(f"[Error] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        agent_loaded=agent is not None
    )

