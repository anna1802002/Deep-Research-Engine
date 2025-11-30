from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body, Path, Query
from fastapi.responses import HTMLResponse, Response
from typing import Dict, List, Optional
import logging
import uuid
from datetime import datetime

from api.models import (
    ReportRequest, ReportResponse, ReportFormat,
    ResearchResult, ContentChunk, ChunkMetadata
)
from api.exceptions import ResourceNotFoundError, BadRequestError
from api.utils import validate_resource_exists

logger = logging.getLogger("deep_research.api.reports")

router = APIRouter(
    prefix="/api",
    tags=["reports"],
)

# In-memory stores (replace with database in production)
research_results = {}
reports = {}


@router.get("/results/{result_id}", response_model=ResearchResult)
async def get_result(
    result_id: str = Path(..., description="ID of the research result")
):
    """Get a research result by ID."""
    result = research_results.get(result_id)
    validate_resource_exists(result, "Result", result_id)
    
    # Return result
    return result


@router.post("/reports", response_model=ReportResponse)
async def create_report(background_tasks: BackgroundTasks, request: ReportRequest):
    """
    Create a report from research results.
    - Generates a report in the requested format
    - Optionally includes citations
    """
    # Check if result exists
    result = research_results.get(request.result_id)
    validate_resource_exists(result, "Result", request.result_id)
    
    # Generate report ID
    report_id = str(uuid.uuid4())
    
    # Create initial report
    report = {
        "report_id": report_id,
        "format": request.format,
        "content": "Report is being generated...",
        "generated_at": datetime.now(),
        "result_id": request.result_id
    }
    
    # Store report
    reports[report_id] = report
    
    # Generate report in background
    background_tasks.add_task(
        generate_report, 
        report_id, 
        request.result_id, 
        request.format,
        request.include_citations,
        request.max_length
    )
    
    # Return initial response
    return ReportResponse(**report)


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str = Path(..., description="ID of the report"),
    raw: bool = Query(False, description="If true, returns raw content with appropriate Content-Type")
):
    """
    Get a generated report.
    - Returns the report in the requested format
    - If raw=True, returns the raw content with appropriate Content-Type
    """
    report = reports.get(report_id)
    validate_resource_exists(report, "Report", report_id)
    
    if raw:
        # Return raw content with appropriate Content-Type
        if report["format"] == ReportFormat.HTML:
            return HTMLResponse(content=report["content"])
        elif report["format"] == ReportFormat.MARKDOWN:
            return Response(
                content=report["content"],
                media_type="text/markdown"
            )
        else:  # JSON format
            return Response(
                content=report["content"],
                media_type="application/json"
            )
    
    # Return full report object
    return report


async def generate_report(
    report_id: str,
    result_id: str,
    format: ReportFormat,
    include_citations: bool,
    max_length: Optional[int]
):
    """
    Generate a report in the background.
    Uses the report generation module.
    """
    try:
        # Get result
        result = research_results[result_id]
        
        # Import report generator
        from src.report_generation.generator import ReportGenerator
        
        # Create generator
        generator = ReportGenerator()
        
        # Generate report content
        if format == ReportFormat.MARKDOWN:
            content = generator._build_report_content(result["query"], result["chunks"])
        elif format == ReportFormat.HTML:
            md_content = generator._build_report_content(result["query"], result["chunks"])
            content = generator._convert_to_html(md_content, result["query"])
        else:  # JSON format
            import json
            content = json.dumps(result, default=str, indent=2)
        
        # Apply max length if specified
        if max_length and len(content) > max_length:
            content = content[:max_length] + "\n\n*Report truncated due to length constraints.*"
        
        # Update report
        reports[report_id]["content"] = content
        reports[report_id]["generated_at"] = datetime.now()
        
        logger.info(f"Report {report_id} generated successfully")
    except Exception as e:
        logger.error(f"Error generating report {report_id}: {str(e)}")
        
        # Update report with error
        if report_id in reports:
            reports[report_id]["content"] = f"Error generating report: {str(e)}"