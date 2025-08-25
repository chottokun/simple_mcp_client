import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app.main import app, get_agent_executor

# Create an async mock agent that we can control in our tests
mock_agent = AsyncMock()


# This function will override the real get_agent_executor dependency
def override_get_agent_executor():
    return mock_agent


# Apply the override to the FastAPI app for all tests in this file
app.dependency_overrides[get_agent_executor] = override_get_agent_executor

# The TestClient needs to be instantiated after the override is in place.
# The lifespan function will run, but get_agent_executor will be our mock.
client = TestClient(app)


# We use pytest.fixture to reset the mock before each test
@pytest.fixture(autouse=True)
def reset_mock_agent():
    """Reset the mock's state before each test."""
    mock_agent.reset_mock()
    yield


def test_chat_endpoint_success():
    """
    Tests the /api/chat endpoint with a successful agent response.
    """
    # Arrange
    agent_output_dict = {
        "answer": "The project requires building a RAG system.",
        "sources": [
            {"document_name": "reqs.md", "snippet": "The system must be a RAG system."}
        ],
    }
    # The endpoint now uses 'ainvoke' and expects a JSON string in the 'output'
    mock_agent.ainvoke.return_value = {"output": json.dumps(agent_output_dict)}
    request_body = {
        "message": "What are the project requirements?",
        "session_id": "test_1",
    }

    # Act
    response = client.post("/api/chat", json=request_body)

    # Assert
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    assert response.json() == agent_output_dict
    mock_agent.ainvoke.assert_called_once_with(
        {"input": "What are the project requirements?"}
    )


def test_chat_endpoint_invalid_json():
    """
    Tests the /api/chat endpoint when the agent returns a non-JSON string.
    """
    # Arrange
    # The endpoint now uses 'ainvoke'
    mock_agent.ainvoke.return_value = {"output": "This is not JSON."}
    request_body = {"message": "A question", "session_id": "test_2"}

    # Act
    response = client.post("/api/chat", json=request_body)

    # Assert
    assert response.status_code == 500
    assert "not valid JSON" in response.json()["detail"]


def test_chat_endpoint_agent_error():
    """
    Tests the /api/chat endpoint when the agent itself raises an exception.
    """
    # Arrange
    # The endpoint now uses 'ainvoke'
    mock_agent.ainvoke.side_effect = Exception("Agent failed to process.")
    request_body = {
        "message": "A question that breaks the agent",
        "session_id": "test_3",
    }

    # Act
    response = client.post("/api/chat", json=request_body)

    # Assert
    assert response.status_code == 500
    assert "Agent failed to process" in response.json()["detail"]
