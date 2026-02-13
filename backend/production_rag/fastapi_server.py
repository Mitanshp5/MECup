"""
FastAPI Server for Production RAG Agent
Provides REST API endpoint for troubleshooting queries.
"""

from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .agent import get_agent

# Global agent instance
agent = None


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str
    query_type: str = ""


class HealthResponse(BaseModel):
    status: str
    agent_loaded: bool


@asynccontextmanager
async def lifespan(app):
    """Initialize agent on startup."""
    global agent
    print("[*] Initializing RAG agent...")
    try:
        agent = get_agent()
        print("[OK] Agent ready!")
    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
    yield
    print("[*] Shutting down...")


router = APIRouter()


@router.post("/api/troubleshoot", response_model=QueryResponse)
async def troubleshoot(request: QueryRequest):
    """Process a troubleshooting query."""
    global agent

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    if agent is None:
        try:
            agent = get_agent()
        except Exception:
            raise HTTPException(status_code=503, detail="Agent not initialized")

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
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        agent_loaded=agent is not None,
    )

