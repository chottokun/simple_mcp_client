import json
import asyncio
from contextlib import asynccontextmanager
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


# --- Agent Lifecycle Management ---
agent_executor_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager to create and clean up the agent executor.
    The agent is created once when the application starts.
    """
    global agent_executor_instance
    print("Application startup: Creating Agent Executor...")
    # Since create_agent_executor is now async, we await it.
    agent_executor_instance = await create_agent_executor()
    print("Agent Executor created successfully.")
    yield
    # Clean up resources if needed on shutdown
    print("Application shutdown.")
    agent_executor_instance = None


# --- FastAPI App Setup ---
app = FastAPI(
    title="Intelligent RAG Chat System - API",
    description="API for the RAG chat system, including tool endpoints.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(tool_router.router, prefix="/tools", tags=["Tools"])

mcp = FastApiMCP(app)
mcp.mount()


# --- Agent Dependency ---
def get_agent_executor():
    """Dependency to get the singleton agent executor instance."""
    if agent_executor_instance is None:
        # This should not happen if the lifespan event handler is working correctly
        raise HTTPException(status_code=500, detail="Agent executor not initialized.")
    return agent_executor_instance


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
        # Use the asynchronous 'ainvoke' method for the agent
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
