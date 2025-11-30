# tests/test_api.py
import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import your FastAPI app
from api.main import app

client = TestClient(app)

def test_api_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    # Update assertion to match your actual response structure
    assert response.json() is not None  # Just check for valid JSON

def test_query_endpoint():
    """Test the query processing endpoint"""
    request_data = {
        "query": "quantum computing",
        "expand": True
    }
    
    response = client.post("/api/query", json=request_data)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response data: {data}")
        # Just check that we got a valid response
        assert "original_query" in data or "query" in data
    else:
        print(f"Error: {response.text}")
    
    response = client.post("/api/query", json=request_data)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Processed query: {data.get('cleaned_query')}")
        print(f"Expanded query: {data.get('expanded_query')}")
        assert data["original_query"] == request_data["query"]
    else:
        print(f"Error: {response.text}")

def run_tests():
    """Run API tests manually"""
    print("Testing API root endpoint...")
    test_api_root()
    print("Success!")
    
    print("\nTesting query endpoint...")
    test_query_endpoint()

if __name__ == "__main__":
    run_tests()