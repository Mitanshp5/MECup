"""
FastAPI Server for Paint Defect Detection System Support Agent

This server provides REST API endpoints for technical support and troubleshooting
assistance for industrial paint job defect detection systems.

The agent has access to comprehensive documentation covering:
- Vision cameras and imaging systems
- Defect detection algorithms and parameters
- PLC controllers and automation
- Error codes and fault diagnostics
- Calibration and maintenance procedures
- Paint application quality issues

Primary Purpose: Troubleshooting system problems and component failures
Secondary Purpose: General technical questions about system operation
"""



import sys

import os

from contextlib import asynccontextmanager



# Add script directory to path if run directly (though now it's a module)

# sys.path.append('./production_rag') 



from fastapi import APIRouter, HTTPException, Depends

from pydantic import BaseModel



from .agent_improved import get_agent



# Global agent instance

agent = None



class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"  # Optional session ID for conversation tracking



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
    """Process a troubleshooting query with conversation history"""
    global agent
    
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    if agent is None:
        msg = "Agent not initialized"
        print(f"[Error] {msg}")
        raise HTTPException(status_code=503, detail=msg)
    
    try:
        print(f"[Query] Session: {request.session_id}, Query: {request.query}")
        response = agent.query(request.query, session_id=request.session_id)
        print(f"[Response] {response[:100]}...")
        return QueryResponse(response=response)

    except Exception as e:

        print(f"[Error] {str(e)}")

        raise HTTPException(status_code=500, detail=str(e))



@router.post("/api/troubleshoot/clear-history")
async def clear_history(session_id: str = "default"):
    """Clear conversation history for a session"""
    global agent
    
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        agent.clear_history(session_id)
        return {"message": f"History cleared for session: {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/troubleshoot/history")
async def get_history(session_id: str = "default"):
    """Get conversation history for a session"""
    global agent
    
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        history = agent.get_history(session_id)
        return {"session_id": session_id, "history": history, "message_count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        agent_loaded=agent is not None
    )



