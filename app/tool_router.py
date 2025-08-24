from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from . import tools


# Define Pydantic models for request bodies
class IngestRequest(BaseModel):
    file_content: str
    file_name: str


class SearchRequest(BaseModel):
    query: str


# Create a new router
router = APIRouter()


@router.post("/ingest", summary="Ingest a document")
def ingest_endpoint(request: IngestRequest):
    """
    Endpoint to ingest a document. It takes file content and a file name,
    processes them, and adds them to the vector store.
    """
    try:
        result = tools.ingest_document(
            file_content=request.file_content, file_name=request.file_name
        )
        return {"message": result}
    except Exception as e:
        # Propagate exceptions as HTTPExceptions for better error visibility in FastAPI
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", summary="Search for data")
def search_endpoint(request: SearchRequest):
    """
    Endpoint to search for relevant data in the vector store based on a query.
    """
    try:
        result = tools.search_data(query=request.query)
        return {"results": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
