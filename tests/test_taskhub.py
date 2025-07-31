import pytest
from fastapi.testclient import TestClient
from taskhub.server import app

def test_sse_inspector_page():
    """
    Tests if the root path returns the MCP Inspector page using TestClient.
    """
    assert app is not None, "FastAPI app could not be created. Check mcp installation."
    client = TestClient(app)
    response = client.get("/sse")
    assert response.status_code == 200
    assert "<title>MCP Inspector</title>" in response.text
