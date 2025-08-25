import os
import json
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from functools import lru_cache

# --- Embedding Function Wrapper for ChromaDB ---
class LangchainEmbeddingFunction(EmbeddingFunction):
    def __init__(self, embedding_model: Embeddings):
        self._embedding_model = embedding_model

    def __call__(self, input: Documents) -> Embeddings:
        return self._embedding_model.embed_documents(input)


# --- Dependency Injection for ChromaDB Client and Collection ---
@lru_cache(maxsize=1)
def get_chroma_collection():
    """
    Initializes and returns the ChromaDB collection.
    Uses lru_cache to ensure it's a singleton.
    """
    print("--- Getting Chroma Collection ---")

    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    # Import manager here to avoid circular dependencies at startup
    from .llm_manager import llm_manager

    # Get the embedding model from the central manager
    embedding_model = llm_manager.get_embedding_model()
    embedding_function = LangchainEmbeddingFunction(embedding_model)

    collection = client.get_or_create_collection(
        name="company_documents",
        embedding_function=embedding_function,
    )
    return collection


# --- Text Splitter ---
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)


def ingest_document(file_content: str, file_name: str) -> str:
    """
    Ingests a document into the vector store.
    Splits the document into chunks and stores them with metadata.
    """
    try:
        collection = get_chroma_collection()
        docs = text_splitter.split_text(file_content)

        if not docs:
            return f"No text to ingest for {file_name}."

        metadatas = [{"source": file_name} for _ in docs]
        ids = [f"{file_name}-{i}" for i, _ in enumerate(docs)]

        collection.add(documents=docs, metadatas=metadatas, ids=ids)
        return f"Successfully ingested {file_name}"
    except Exception as e:
        return f"Error ingesting {file_name}: {e}"


def search_data(query: str) -> str:
    """
    Searches for relevant documents in the vector store based on a query.

    Returns:
        A JSON string containing the search results, including content and sources.
    """
    try:
        collection = get_chroma_collection()
        results = collection.query(query_texts=[query], n_results=2)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            return json.dumps(
                {"content": "No relevant documents found.", "sources": []}
            )

        # Prepare structured data for the agent
        sources_list = []
        content_list = []
        for i, doc in enumerate(documents):
            source_name = metadatas[i].get("source", "Unknown")
            sources_list.append({"document_name": source_name, "snippet": doc})
            content_list.append(f"Source: {source_name}, Content: {doc}")

        # Return a JSON string so the LLM can easily parse it
        return json.dumps(
            {"content_for_llm": "\n---\n".join(content_list), "sources": sources_list}
        )
    except Exception as e:
        return json.dumps({"error": f"Error searching data: {e}", "sources": []})
