"""
Temporary Chunking Service

This module provides a simple chunking implementation that can be used for demo purposes
until the full implementation from Ticket #8 is available. It follows the interface 
defined in chunk_interface_spec.py so it can be easily replaced later.
"""

from src.chunking.chunker_interface import ChunkerInterface
import re
import hashlib
from typing import List, Dict, Any

class TemporaryChunker(ChunkerInterface):
    """
    Temporary chunking implementation until the external module is available.
    """
    
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def create_chunks(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split content into chunks based on size or natural divisions."""
        if not content or "text" not in content:
            return []
        
        text = content["text"]
        metadata = content.get("metadata", {}).copy()
        
        # Generate document ID if not provided
        if "document_id" not in metadata:
            doc_id = hashlib.md5((text[:100] + str(metadata.get("url", ""))).encode()).hexdigest()
            metadata["document_id"] = doc_id
        
        # If text is short enough, return as single chunk
        if len(text) <= self.chunk_size:
            return [self._create_chunk(text, metadata, 0, 1)]
        
        # Split by paragraphs
        chunks = []
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding paragraph exceeds chunk size and we have content
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                # Store current chunk
                chunks.append(self._create_chunk(current_chunk, metadata, chunk_index, None))
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + "\n\n" + paragraph
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, metadata, chunk_index, None))
        
        # Update total chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk["metadata"]["total_chunks"] = total_chunks
        
        return chunks
    
    def _create_chunk(self, text, metadata, chunk_index, total_chunks):
        """Create a chunk with proper metadata."""
        chunk_metadata = metadata.copy()
        
        # Generate chunk ID
        chunk_id = f"{metadata.get('document_id', 'doc')}-chunk{chunk_index}"
        
        # Add chunk-specific metadata
        chunk_metadata.update({
            "chunk_id": chunk_id,
            "chunk_index": chunk_index
        })
        
        if total_chunks is not None:
            chunk_metadata["total_chunks"] = total_chunks
        
        return {
            "text": text,
            "metadata": chunk_metadata
        }