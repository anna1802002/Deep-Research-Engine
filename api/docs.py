# api/docs.py
"""
API Documentation for Deep Research Engine

This file serves as a reference for all API endpoints and usage.
It can be used to generate standalone documentation.
"""

# API Overview
OVERVIEW = """
# Deep Research Engine API

The Deep Research Engine API provides access to advanced research capabilities,
allowing you to retrieve, rank, and extract relevant data from multiple sources.

## Base URL

All API endpoints are relative to the base URL:
https://api.deepresearchengine.com/

## Authentication

Most endpoints require an API key. Include your API key in the `X-API-Key` header:
X-API-Key: your-api-key-here

## Rate Limits

The API has a rate limit of 100 requests per minute. If you exceed this limit,
you will receive a 429 response with a `Retry-After` header.

## Error Handling

All errors return a JSON response with the following structure:

{
  "error": {
    "status_code": 400,
    "detail": "Error message"
  }
}

Common error codes:

- 400: Bad Request
- 401: Unauthorized (invalid or missing API key)
- 404: Resource Not Found
- 422: Validation Error
- 429: Rate Limit Exceeded
- 500: Internal Server Error
"""

# API Endpoints
ENDPOINTS = """
## API Endpoints

### Query Processing

#### POST /api/query
Process a research query by cleaning it and optionally expanding it with related terms.

Request:
{
  "query": "quantum computing cryptography",
  "expand": true
}

Response:
{
  "original_query": "quantum computing cryptography",
  "cleaned_query": "quantum computing cryptography",
  "expanded_query": "quantum computing, cryptography, qubits, encryption, post-quantum, Shor's algorithm, quantum key distribution, RSA",
  "related_terms": [
    "quantum computing", "cryptography", "qubits", "encryption", 
    "post-quantum", "Shor's algorithm", "quantum key distribution", "RSA"
  ]
}

### Research

#### POST /api/research
Start an asynchronous research job based on a query.

Request:
{
  "query": "quantum computing cryptography",
  "sources": ["all"],
  "max_results": 50,
  "include_content": true
}

Response:
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "pending",
  "created_at": "2024-03-21T10:30:00Z",
  "estimated_completion": "2024-03-21T10:32:00Z"
}

#### GET /api/status/{job_id}
Check the status of an asynchronous research job.

Response:
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "completed",
  "progress": 1.0,
  "message": "Research completed successfully",
  "created_at": "2024-03-21T10:30:00Z",
  "updated_at": "2024-03-21T10:32:00Z",
  "estimated_completion": "2024-03-21T10:32:00Z",
  "result_id": "a1b2c3d4-e5f6-4a5b-8c7d-1e2f3a4b5c6d"
}

### Results & Reports

#### GET /api/results/{result_id}
Retrieve the results of a completed research job.

Response:
{
  "query": "quantum computing cryptography",
  "timestamp": "2024-03-21T10:32:00Z",
  "total_chunks": 3,
  "sources_used": ["ArXiv", "Web Search", "Google Scholar"],
  "chunks": [
    {
      "text": "Quantum computing poses significant challenges to traditional cryptography methods...",
      "metadata": {
        "source": "ArXiv",
        "url": "https://arxiv.org/abs/sample123",
        "title": "The Impact of Quantum Computing on Modern Cryptography",
        "publication_date": "2024-02-20T00:00:00Z",
        "authors": ["Jane Smith", "John Doe"],
        "relevance_score": 0.92,
        "authority_score": 0.85,
        "recency_score": 0.78,
        "final_score": 0.87
      }
    }
  ],
  "report_id": null
}

#### POST /api/reports
Generate a formatted report from research results.

Request:
{
  "result_id": "a1b2c3d4-e5f6-4a5b-8c7d-1e2f3a4b5c6d",
  "format": "markdown",
  "include_citations": true,
  "max_length": null
}

Response:
{
  "report_id": "b2c3d4e5-f6a7-5b6c-9d8e-2f3a4b5c6d7e",
  "format": "markdown",
  "content": "Report is being generated...",
  "generated_at": "2024-03-21T10:33:00Z",
  "result_id": "a1b2c3d4-e5f6-4a5b-8c7d-1e2f3a4b5c6d"
}

#### GET /api/reports/{report_id}
Retrieve a generated report.

Parameters:
- raw (boolean, query parameter): If true, returns raw content with appropriate Content-Type.

Response:
{
  "report_id": "b2c3d4e5-f6a7-5b6c-9d8e-2f3a4b5c6d7e",
  "format": "markdown",
  "content": "# Research Report: quantum computing cryptography\\n\\nGenerated on 2024-03-21 10:33:45\\n\\n## Summary\\nThis report contains the top 3 most relevant excerpts from various sources related to your query.\\n\\n...",
  "generated_at": "2024-03-21T10:33:45Z",
  "result_id": "a1b2c3d4-e5f6-4a5b-8c7d-1e2f3a4b5c6d"
}
"""

# Code Examples
CODE_EXAMPLES = """
## Code Examples

### Python Example

```python
import requests
import time
import json

# Base URL and API key
BASE_URL = "https://api.deepresearchengine.com"
API_KEY = "your-api-key-here"

# Headers
headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Step 1: Process the query
def process_query(query, expand=True):
    response = requests.post(
        f"{BASE_URL}/api/query",
        headers=headers,
        json={"query": query, "expand": expand}
    )
    return response.json()

# Step 2: Start a research job
def start_research(query, sources=["all"], max_results=50):
    response = requests.post(
        f"{BASE_URL}/api/research",
        headers=headers,
        json={
            "query": query,
            "sources": sources,
            "max_results": max_results,
            "include_content": True
        }
    )
    return response.json()

# Step 3: Check job status until complete
def wait_for_completion(job_id, poll_interval=2):
    while True:
        response = requests.get(
            f"{BASE_URL}/api/status/{job_id}",
            headers=headers
        )
        status_data = response.json()
        
        if status_data["status"] == "completed":
            return status_data["result_id"]
        elif status_data["status"] == "failed":
            raise Exception(f"Research job failed: {status_data['message']}")
        
        # Print progress and wait
        print(f"Progress: {int(status_data['progress'] * 100)}%")
        time.sleep(poll_interval)

# Step 4: Get research results
def get_results(result_id):
    response = requests.get(
        f"{BASE_URL}/api/results/{result_id}",
        headers=headers
    )
    return response.json()

# Step 5: Generate a report
def generate_report(result_id, format="markdown"):
    response = requests.post(
        f"{BASE_URL}/api/reports",
        headers=headers,
        json={
            "result_id": result_id,
            "format": format,
            "include_citations": True
        }
    )
    return response.json()

# Step 6: Get the final report
def get_report(report_id, raw=False):
    params = {"raw": "true" if raw else "false"}
    response = requests.get(
        f"{BASE_URL}/api/reports/{report_id}",
        headers=headers,
        params=params
    )
    return response.json() if not raw else response.text

# Full example
def run_research_pipeline(query):
    print(f"Researching: {query}")
    
    # Process query
    processed = process_query(query)
    print(f"Processed query: {processed['cleaned_query']}")
    
    # Start research
    job = start_research(processed['cleaned_query'])
    print(f"Started research job: {job['job_id']}")
    
    # Wait for completion
    result_id = wait_for_completion(job['job_id'])
    print(f"Research complete! Result ID: {result_id}")
    
    # Get results
    results = get_results(result_id)
    print(f"Found {results['total_chunks']} relevant chunks from {len(results['sources_used'])} sources")
    
    # Generate report
    report_data = generate_report(result_id, format="markdown")
    print(f"Report generation started: {report_data['report_id']}")
    
    # Wait a moment for report generation
    time.sleep(5)
    
    # Get the final report
    report = get_report(report_data['report_id'], raw=True)
    
    # Save report to file
    with open("research_report.md", "w") as f:
        f.write(report)
    
    print("Report saved to research_report.md")

# Run the pipeline
if __name__ == "__main__":
    run_research_pipeline("quantum computing cryptography")" \
    """""

def get_api_documentation():
    """Return the complete API documentation."""
    return OVERVIEW + ENDPOINTS + CODE_EXAMPLES