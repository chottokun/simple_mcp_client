import json
from unittest.mock import MagicMock, patch
from app.tools import ingest_document, search_data


@patch("app.tools.get_chroma_collection")
def test_ingest_document_success(mock_get_collection):
    """
    Tests that `ingest_document` correctly processes a document,
    splits it into chunks, and adds it to the vector store.
    """
    # Arrange
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection

    file_content = (
        "This is a test document. It has multiple sentences to test splitting."
    )
    file_name = "test.txt"

    # Act
    result = ingest_document(file_content=file_content, file_name=file_name)

    # Assert
    assert result == f"Successfully ingested {file_name}"
    mock_get_collection.assert_called_once()
    mock_collection.add.assert_called_once()

    # Check the arguments passed to the 'add' method
    args, kwargs = mock_collection.add.call_args
    assert "documents" in kwargs
    assert "metadatas" in kwargs
    assert "ids" in kwargs

    documents = kwargs["documents"]
    metadatas = kwargs["metadatas"]
    ids = kwargs["ids"]

    # Based on the RecursiveCharacterTextSplitter logic
    expected_doc = (
        "This is a test document. It has multiple sentences to test splitting."
    )
    assert len(documents) == 1
    assert documents[0] == expected_doc
    assert metadatas[0] == {"source": file_name}
    assert ids[0] == f"{file_name}-0"


@patch("app.tools.get_chroma_collection")
def test_search_data_success(mock_get_collection):
    """
    Tests that `search_data` correctly queries the vector store
    and returns formatted results.
    """
    # Arrange
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection

    query = "What is this document about?"

    # Configure the mock query result from ChromaDB
    mock_query_result = {
        "documents": [["This is a test document."]],
        "metadatas": [[{"source": "test.txt"}]],
        "ids": [["test.txt-0"]],
        "distances": [[0.1]],
    }
    mock_collection.query.return_value = mock_query_result

    # Act
    result = search_data(query=query)

    # Assert
    mock_get_collection.assert_called_once()
    mock_collection.query.assert_called_once_with(query_texts=[query], n_results=2)

    # Check the formatted output
    assert "Source: test.txt" in result
    assert "Content: This is a test document." in result


@patch("app.tools.get_chroma_collection")
def test_search_data_no_results(mock_get_collection):
    """
    Tests that `search_data` handles cases with no results gracefully.
    """
    # Arrange
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection

    query = "non-existent query"

    # Configure an empty mock query result
    mock_query_result = {
        "documents": [[]],
        "metadatas": [[]],
    }
    mock_collection.query.return_value = mock_query_result

    # Act
    result = search_data(query=query)

    # Assert
    expected_json = json.dumps(
        {"content": "No relevant documents found.", "sources": []}
    )
    assert result == expected_json
