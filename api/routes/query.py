from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Path, Query
from typing import Optional, List
import logging
import asyncio
import uuid
from datetime import datetime, timedelta

from api.models import (
    QueryRequest, QueryResponse,
    ResearchRequest, JobResponse, ResearchStatus
)
from api.exceptions import ResourceNotFoundError, BadRequestError
from api.utils import validate_resource_exists

# Import modules
from src.query_processing.parser import QueryParser
from src.query_processing.expander import QueryExpander

logger = logging.getLogger("deep_research.api.query")

router = APIRouter(
    prefix="/api",
    tags=["query"],
)

# In-memory job store (replace with database in production)
jobs = {}


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a research query.
    - Cleans the query
    - Optionally expands it with related terms
    """
    try:
        # Initialize query processors
        parser = QueryParser()
        
        # Clean query
        cleaned_query = parser.clean_query(request.query)
        
        # Create response
        response = QueryResponse(
            original_query=request.query,
            cleaned_query=cleaned_query
        )
        
        # Expand query if requested
        if request.expand:
            expander = QueryExpander()
            expanded_query = expander.expand_query(cleaned_query)
            
            # Populate expansion results
            response.expanded_query = expanded_query
            # Extract related terms (from comma-separated list)
            related_terms = [term.strip() for term in expanded_query.split(',')]
            response.related_terms = related_terms
        
        return response
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/research", response_model=JobResponse)
async def start_research(background_tasks: BackgroundTasks, request: ResearchRequest):
    """
    Start a research job.
    - Processes the query
    - Fetches data from selected sources
    - Returns a job ID for status tracking
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job
        job = {
            "job_id": job_id,
            "status": ResearchStatus.PENDING,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "query": request.query,
            "sources": [source.value for source in request.sources],
            "max_results": request.max_results,
            "include_content": request.include_content,
            "result_id": None,
            "error": None,
            "progress": 0.0,
            "estimated_completion": datetime.now() + timedelta(minutes=2)  # Estimate
        }
        
        # Store job
        jobs[job_id] = job
        
        # Start research in background
        background_tasks.add_task(run_research_job, job_id, request)
        
        # Return job response
        return JobResponse(
            job_id=job_id,
            status=ResearchStatus.PENDING,
            created_at=job["created_at"],
            estimated_completion=job["estimated_completion"]
        )
    except Exception as e:
        logger.error(f"Error starting research: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting research: {str(e)}")


@router.get("/status/{job_id}")
async def check_status(
    job_id: str = Path(..., description="The ID of the job to check")
):
    """Check the status of a research job."""
    job = jobs.get(job_id)
    validate_resource_exists(job, "Job", job_id)
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0.0),
        "message": job.get("message", ""),
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "estimated_completion": job.get("estimated_completion"),
        "result_id": job.get("result_id")
    }


async def run_research_job(job_id: str, request: ResearchRequest):
    """
    Run the research job in the background.
    
    This would normally use the orchestrator to:
    1. Process the query
    2. Fetch data from sources
    3. Rank and extract results
    4. Store results
    """
    try:
        # Update job status
        jobs[job_id]["status"] = ResearchStatus.IN_PROGRESS
        jobs[job_id]["updated_at"] = datetime.now()
        jobs[job_id]["message"] = "Starting research..."
        
        # Process query
        parser = QueryParser()
        expander = QueryExpander()
        
        cleaned_query = parser.clean_query(request.query)
        expanded_query = expander.expand_query(cleaned_query)
        
        # Update job
        jobs[job_id]["progress"] = 0.1
        jobs[job_id]["message"] = "Query processed"
        jobs[job_id]["updated_at"] = datetime.now()
        
        # Import necessary modules here to avoid circular imports
        from src.data_retrieval.mcp_client import MCPClient
        
        # Use MCP client instead of orchestrator
        mcp_client = MCPClient()
        
        # Update job
        jobs[job_id]["progress"] = 0.2
        jobs[job_id]["message"] = "Retrieving data from sources..."
        jobs[job_id]["updated_at"] = datetime.now()
        
        # Get data from MCP
        mcp_response = await mcp_client.process_query(expanded_query)
        
        # Update job
        jobs[job_id]["progress"] = 0.6
        jobs[job_id]["message"] = "Ranking content..."
        jobs[job_id]["updated_at"] = datetime.now()
        
        # Import ranking system
        from src.ranking.ranking_system import RankingSystem
        
        # Rank content
        ranking_system = RankingSystem()
        ranked_chunks = ranking_system.rank_content(
            query={"text": cleaned_query, "metadata": {}}, 
            chunks=mcp_response.get("chunks", []),
            top_n=request.max_results
        )
        
        # Generate result ID
        result_id = str(uuid.uuid4())
        
        # Create result object (would normally be stored in database)
        result = {
            "query": request.query,
            "timestamp": datetime.now(),
            "total_chunks": len(ranked_chunks),
            "sources_used": list(set(chunk.get("metadata", {}).get("source", "Unknown") 
                                for chunk in ranked_chunks)),
            "chunks": ranked_chunks,
            "report_id": None
        }
        
        # Store result (would normally be in database)
        # In this simplified version, we're using a global dictionary
        from api.routes.reports import research_results
        research_results[result_id] = result
        
        # Update job with completion
        jobs[job_id]["status"] = ResearchStatus.COMPLETED
        jobs[job_id]["progress"] = 1.0
        jobs[job_id]["message"] = "Research completed successfully"
        jobs[job_id]["updated_at"] = datetime.now()
        jobs[job_id]["result_id"] = result_id
        
        logger.info(f"Research job {job_id} completed successfully, result_id: {result_id}")
    except Exception as e:
        logger.error(f"Error in research job {job_id}: {str(e)}")
        
        # Update job with error
        if job_id in jobs:
            jobs[job_id]["status"] = ResearchStatus.FAILED
            jobs[job_id]["error"] = str(e)
            jobs[job_id]["updated_at"] = datetime.now()
            jobs[job_id]["message"] = f"Error: {str(e)}"