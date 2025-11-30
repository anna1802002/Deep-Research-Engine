from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Valid source types for research queries."""
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    GOOGLE_SCHOLAR = "google_scholar"
    WEB = "web"
    ALL = "all"


class QueryRequest(BaseModel):
    """Model for query processing request."""
    query: str = Field(..., description="The research query to process")
    expand: bool = Field(True, description="Whether to expand the query with related terms")


class QueryResponse(BaseModel):
    """Model for query processing response."""
    original_query: str
    cleaned_query: str
    expanded_query: Optional[str] = None
    related_terms: Optional[List[str]] = None


class ResearchRequest(BaseModel):
    """Model for research request."""
    query: str = Field(..., description="The research query to process")
    sources: List[SourceType] = Field(default=[SourceType.ALL], description="Sources to search")
    max_results: int = Field(default=50, description="Maximum number of results to return")
    include_content: bool = Field(default=True, description="Whether to include full content")


class ResearchStatus(str, Enum):
    """Valid status values for research jobs."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    """Model for job creation response."""
    job_id: str
    status: ResearchStatus
    created_at: datetime
    estimated_completion: Optional[datetime] = None


class StatusResponse(BaseModel):
    """Model for job status response."""
    job_id: str
    status: ResearchStatus
    progress: Optional[float] = None
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None
    result_id: Optional[str] = None


class ChunkMetadata(BaseModel):
    """Metadata for content chunks."""
    source: str
    url: Optional[str] = None
    title: Optional[str] = None
    publication_date: Optional[datetime] = None
    authors: Optional[List[str]] = None
    relevance_score: Optional[float] = None
    authority_score: Optional[float] = None
    recency_score: Optional[float] = None
    final_score: Optional[float] = None


class ContentChunk(BaseModel):
    """Model for content chunks."""
    text: str
    metadata: ChunkMetadata


class ResearchResult(BaseModel):
    """Model for research results."""
    query: str
    timestamp: datetime
    total_chunks: int
    sources_used: List[str]
    chunks: List[ContentChunk]
    report_id: Optional[str] = None


class ReportFormat(str, Enum):
    """Valid report formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class ReportRequest(BaseModel):
    """Model for report generation request."""
    result_id: str
    format: ReportFormat = ReportFormat.MARKDOWN
    include_citations: bool = True
    max_length: Optional[int] = None


class ReportResponse(BaseModel):
    """Model for report response."""
    report_id: str
    format: ReportFormat
    content: str
    generated_at: datetime
    result_id: str