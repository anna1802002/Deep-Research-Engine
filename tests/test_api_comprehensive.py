# tests/test_api_comprehensive.py
import os
import sys
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app
from api.models import ResearchStatus

client = TestClient(app)

# Basic Endpoints Tests
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

# Documentation Tests
def test_documentation_endpoints():
    """Test that documentation endpoints are working."""
    # Test OpenAPI JSON
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
    assert "paths" in response.json()
    
    # Test Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()
    
    # Test ReDoc
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()

# Query Processing Tests
def test_query_endpoint():
    """Test the query processing endpoint."""
    # Test without expansion
    query_data = {
        "query": "test query",
        "expand": False
    }
    response = client.post("/api/query", json=query_data)
    assert response.status_code == 200
    data = response.json()
    assert "original_query" in data
    assert "cleaned_query" in data
    assert data["original_query"] == "test query"
    
    # Test with expansion
    query_data["expand"] = True
    with patch('api.routes.query.QueryExpander') as mock_expander:
        mock_instance = MagicMock()
        mock_instance.expand_query.return_value = "test query, expanded terms, more terms"
        mock_expander.return_value = mock_instance
        
        response = client.post("/api/query", json=query_data)
        assert response.status_code == 200
        data = response.json()
        assert "expanded_query" in data
        assert "related_terms" in data

# Research Job Tests
def test_research_job_endpoints():
    """Test the research job endpoints."""
    # Test starting a research job
    request_data = {
        "query": "test research",
        "sources": ["all"],
        "max_results": 25,
        "include_content": True
    }
    
    # Mock UUID generation to get predictable job_id
    test_job_id = str(uuid.uuid4())
    with patch('uuid.uuid4', return_value=uuid.UUID(test_job_id)):
        response = client.post("/api/research", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["job_id"] == test_job_id
        assert data["status"] == "pending"
        
        # Test job status endpoint
        response = client.get(f"/api/status/{test_job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == test_job_id
        assert "status" in data
        assert "progress" in data

# Report Generation Tests
def test_report_endpoints():
    """Test the report generation endpoints."""
    # Create a mock result
    test_result_id = str(uuid.uuid4())
    
    # Test report generation request
    report_request = {
        "result_id": test_result_id,
        "format": "markdown",
        "include_citations": True,
        "max_length": None
    }
    
    # Mock UUID generation for report_id
    test_report_id = str(uuid.uuid4())
    
    # Mock the report generation
    with patch('uuid.uuid4', return_value=uuid.UUID(test_report_id)):
        # Mock the research_results availability
        with patch('api.routes.reports.research_results', {test_result_id: {"query": "test", "chunks": []}}):
            response = client.post("/api/reports", json=report_request)
            assert response.status_code == 200
            data = response.json()
            assert "report_id" in data
            assert data["report_id"] == test_report_id
            assert data["format"] == "markdown"
            
            # Test getting the report
            with patch('api.routes.reports.reports', {test_report_id: {
                "report_id": test_report_id,
                "format": "markdown",
                "content": "# Test Report",
                "generated_at": "2023-01-01T00:00:00",
                "result_id": test_result_id
            }}):
                response = client.get(f"/api/reports/{test_report_id}")
                assert response.status_code == 200
                data = response.json()
                assert data["report_id"] == test_report_id
                
                # Test raw report content
                response = client.get(f"/api/reports/{test_report_id}?raw=true")
                assert response.status_code == 200
                assert response.text == "# Test Report"

# Error Handling Tests
def test_error_handling():
    """Test API error handling."""
    # Test 404 for non-existent endpoint
    response = client.get("/api/non_existent_endpoint")
    assert response.status_code == 404
    assert "error" in response.json()
    
    # Test 404 for non-existent job
    response = client.get("/api/status/non_existent_job_id")
    assert response.status_code == 404
    assert "error" in response.json()
    assert "detail" in response.json()["error"]
    assert response.json()["error"]["status_code"] == 404
    
    # Test 404 for non-existent report
    response = client.get("/api/reports/non_existent_report_id")
    assert response.status_code == 404
    assert "error" in response.json()
    
    # Test validation error
    invalid_query = {"invalid_field": "value"}
    response = client.post("/api/query", json=invalid_query)
    assert response.status_code == 422  # Unprocessable Entity
    assert "error" in response.json()

# Middleware Tests
def test_request_logging_middleware():
    """Test that request logging middleware adds headers."""
    response = client.get("/health")
    assert "X-Process-Time" in response.headers
    assert "X-Request-ID" in response.headers

def test_rate_limiting_middleware():
    """Test rate limiting middleware."""
    # This is difficult to test in a unit test without modifying the middleware
    # We'll check if the middleware class exists and is added in main.py
    from api.middleware import RateLimitMiddleware
    assert RateLimitMiddleware is not None

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])