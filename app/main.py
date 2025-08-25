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
    print("--- Getting Agent Executor ---")
    return create_agent_executor()


# --- API Endpoints ---
@app.get("/", tags=["Health"])
async def read_root():
    """A simple health check endpoint."""
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(
    request: ChatRequest, agent_executor: Annotated[Any, Depends(get_agent_executor)]
):
    """
    Receives a user's message, processes it with the LangChain agent,
    and returns a structured answer with sources.
    """
    try:
        # Since the endpoint is async, we should use ainvoke to not block the event loop
        # For AgentExecutor, this runs the synchronous 'invoke' in a thread pool.
        result = await agent_executor.ainvoke({"input": request.message})
        output_str = result.get("output", "{}")

        # The output from the agent should be a JSON string, load it
        response_data = json.loads(output_str)
        return ChatResponse(**response_data)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"The agent returned a response that was not valid JSON. Response: {output_str}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
