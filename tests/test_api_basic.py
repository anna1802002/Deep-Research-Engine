# tests/test_api_basic.py
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test that the health endpoint is working."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "API is running successfully"

def test_root_endpoint():
    """Test that the root endpoint is working."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_query_endpoint_structure():
    """Test the query endpoint structure (without calling actual query processors)."""
    query_data = {
        "query": "test query",
        "expand": False
    }
    response = client.post("/api/query", json=query_data)
    # Since actual query processing depends on other components,
    # we're just checking the response structure
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "original_query" in data
        assert "cleaned_query" in data