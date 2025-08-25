import json
from typing import Dict
from unittest.mock import MagicMock

from .config import config
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_ollama import OllamaLLM
from langchain_ollama import OllamaEmbeddings


class LLMManager:
    """
    A singleton manager for LLM and Embedding clients.
    This ensures that clients are instantiated only once and provides a central point for mocking.
    """
    _instance = None
    _llm: BaseLanguageModel = None
    _embedding_model: Embeddings = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LLMManager, cls).__new__(cls)
        return cls._instance

    def get_llm(self) -> BaseLanguageModel:
        """Gets the chat LLM, creating it if it doesn't exist."""
        if self._llm is None:
            print("--- Initializing LLM ---")
            if config.MOCK_OLLAMA:
                print("--- Using Mock LLM ---")
                self._llm = self._create_mock_llm()
            else:
                self._llm = OllamaLLM(
                    model=config.OLLAMA_CHAT_MODEL,
                    base_url=config.OLLAMA_BASE_URL
                )
        return self._llm

    def get_embedding_model(self) -> Embeddings:
        """Gets the embedding model, creating it if it doesn't exist."""
        if self._embedding_model is None:
            print("--- Initializing Embedding Model ---")
            if config.MOCK_OLLAMA:
                print("--- Using Mock Embeddings ---")
                self._embedding_model = self._create_mock_embedding_model()
            else:
                self._embedding_model = OllamaEmbeddings(
                    model=config.OLLAMA_EMBED_MODEL,
                    base_url=config.OLLAMA_BASE_URL
                )
        return self._embedding_model

    def _create_mock_llm(self) -> MagicMock:
        """Creates a sophisticated mock LLM for testing."""
        mock_llm = MagicMock(spec=OllamaLLM)

        def llm_side_effect(prompt: str) -> str:
            print(f"\n--- Mock LLM received prompt ---\n{prompt}\n---------------------------------")
            if "Observation:" in prompt:
                final_answer_json = json.dumps({
                    "answer": "This is a mocked answer based on a tool's observation.",
                    "sources": [{"document_name": "mock_retrieved_source.txt", "snippet": "Mocked snippet from the source."}]
                })
                return f"Thought: I have the answer now.\nFinal Answer: {final_answer_json}"
            else:
                return 'Thought: I need to use a tool to answer this.\nAction: local_document_search\nAction Input: "What is this document about?"'

        mock_llm.invoke.side_effect = llm_side_effect
        return mock_llm

    def _create_mock_embedding_model(self) -> MagicMock:
        """Creates a mock embedding model that returns correct-shaped vectors."""
        mock_embed_model = MagicMock(spec=OllamaEmbeddings)

        def embed_documents_side_effect(documents: list[str]) -> list[list[float]]:
            print(f"--- Mock embedding {len(documents)} documents ---")
            return [[0.1] * 128 for _ in documents]

        mock_embed_model.embed_documents.side_effect = embed_documents_side_effect
        return mock_embed_model

# Create a single, globally accessible instance
llm_manager = LLMManager()
