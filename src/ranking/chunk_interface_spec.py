"""
Chunk Interface Specification

This file provides documentation on the expected format for chunks that will be passed
to the Content Ranking System. This interface is what we expect the implementation of
Ticket #8 (Chunk Extraction & Metadata Processing) to provide.

No code is executed from this file - it serves purely as documentation.
"""

from typing import Dict, List, TypedDict, Optional, Union


class ChunkMetadata(TypedDict, total=False):
    """
    TypedDict defining the expected structure of chunk metadata.
    Fields marked as required are essential for ranking functionality.
    """
    
    # Required Fields
    chunk_id: str                      # Unique identifier for this chunk
    document_id: str                   # ID of source document
    url: str                           # Source URL
    
    # Important for Ranking (but could have defaults)
    source_type: str                   # e.g., 'academic', 'web', 'government'
    publication_date: str              # ISO format date (YYYY-MM-DD)
    
    # Optional Additional Fields
    title: Optional[str]               # Title or heading of the section
    authors: Optional[List[str]]       # List of author names
    citation_count: Optional[int]      # Number of citations (for academic papers)
    domain_authority: Optional[float]  # Pre-computed authority score
    content_type: Optional[str]        # e.g., 'text', 'table', 'code'
    
    # Added by Ranking System (do not provide these)
    embedding: Optional[List[float]]   # Vector embedding (added by ranking system)
    relevance_score: Optional[float]   # Computed relevance score
    authority_score: Optional[float]   # Computed authority score
    recency_score: Optional[float]     # Computed recency score
    final_score: Optional[float]       # Final combined ranking score


class ContentChunk(TypedDict):
    """
    TypedDict defining the expected structure of a content chunk.
    This is the expected format that the Chunk Extraction module (Ticket #8)
    will provide to the Content Ranking System (Ticket #7).
    """
    text: str                          # The actual text content of the chunk
    metadata: ChunkMetadata            # Metadata associated with this chunk


# Example of a properly formatted chunk:
EXAMPLE_CHUNK = {
    "text": "Quantum computing poses significant challenges to traditional cryptography methods. "
           "RSA and ECC may become vulnerable to Shor's algorithm when large-scale quantum computers "
           "become available.",
    "metadata": {
        "chunk_id": "doc123-chunk02",
        "document_id": "doc123",
        "url": "https://arxiv.org/abs/2105.12345",
        "source_type": "academic",
        "publication_date": "2023-05-15",
        "title": "Effects of Quantum Computing on Modern Cryptography",
        "authors": ["Jane Smith", "John Doe"],
        "citation_count": 42,
        "content_type": "text"
    }
}


# Interface Requirements

def rank_chunks(query: str, chunks: List[ContentChunk], top_n: int = 10) -> List[ContentChunk]:
    """
    Example function signature showing how the ranking system will consume chunks.
    
    Args:
        query: The search/research query string
        chunks: List of content chunks from the Chunk Extraction module
        top_n: Number of top-ranked chunks to return
        
    Returns:
        Ranked list of chunks with scoring metadata added
    """
    # This is just an interface definition, not actual implementation
    pass