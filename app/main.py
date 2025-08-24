import json
from functools import lru_cache
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Annotated

from . import tool_router
from .agent import create_agent_executor
from fastapi_mcp import FastApiMCP


# --- Pydantic Models for Chat API ---
class ChatRequest(BaseModel):
    message: str
    session_id: str
    history: List[Dict[str, Any]] = Field(default_factory=list)


class Source(BaseModel):
    document_name: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]


# --- FastAPI App Setup ---
app = FastAPI(
    title="Intelligent RAG Chat System - API",
    description="API for the RAG chat system, including tool endpoints.",
    version="0.1.0",
)

app.include_router(tool_router.router, prefix="/tools", tags=["Tools"])

mcp = FastApiMCP(app)
mcp.mount()


# --- Agent Dependency ---
@lru_cache(maxsize=1)
def get_agent_executor():
    """Dependency to get a singleton agent executor instance."""
    return create_agent_executor()


# --- API Endpoints ---
@app.get("/", tags=["Health"])
def read_root():
    """A simple health check endpoint."""
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
def chat_endpoint(
    request: ChatRequest, agent_executor: Annotated[Any, Depends(get_agent_executor)]
):
    """
    Receives a user's message, processes it with the LangChain agent,
    and returns a structured answer with sources.
    """
    try:
        result = agent_executor.invoke({"input": request.message})
        output_str = result.get("output", "{}")
        response_data = json.loads(output_str)
        return ChatResponse(**response_data)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="The agent returned a response that was not valid JSON.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
