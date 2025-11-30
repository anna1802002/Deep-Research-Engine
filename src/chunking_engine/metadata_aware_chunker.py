# src/chunking_engine/metadata_aware_chunker.py

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to sys.path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import chunking components
from chunking_engine.dynamic_chunker import DynamicChunker, ChunkEntry

# Import metadata components
from metadata_processing.metadata_extractor import MetadataExtractor
from metadata_processing.metadata_standardizer import MetadataStandardizer
from metadata_processing.metadata_validator import MetadataValidator
from metadata_processing.metadata_processor import MetadataProcessor
from metadata_processing.metadata_integration import MetadataIntegrationService

# Set up logging
logger = logging.getLogger("deep_research.chunking_engine.metadata_aware_chunker")

class EnhancedChunkEntry(ChunkEntry):
    """
    Enhanced chunk entry that includes rich metadata from the metadata processing system.
    """
    def __init__(self, chunk_id, document_id, content, start_index, end_index, 
                 metadata, rich_metadata=None):
        super().__init__(chunk_id, document_id, content, start_index, end_index, metadata)
        self.rich_metadata = rich_metadata or {}
        
        # Merge rich metadata into regular metadata
        if rich_metadata:
            for key, value in rich_metadata.items():
                if key not in self.metadata:
                    self.metadata[key] = value

    def to_dict(self):
        """Convert to dictionary including all metadata"""
        base_dict = vars(self)
        # Remove rich_metadata from output to avoid duplication
        if 'rich_metadata' in base_dict:
            del base_dict['rich_metadata']
        return base_dict


class MetadataAwareChunker:
    """
    Chunker that integrates with the metadata processing system.
    This chunker ensures each chunk has appropriate metadata from the document.
    """
    
    def __init__(self):
        """Initialize the metadata-aware chunker."""
        self.dynamic_chunker = DynamicChunker()
        self.metadata_service = MetadataIntegrationService()
        logger.info("Initialized MetadataAwareChunker")
    
    def process_document(self, content: str, metadata: Optional[Dict] = None, 
                         chunking_method: str = "Auto-detect",
                         source_type: Optional[str] = None) -> List[EnhancedChunkEntry]:
        """
        Process a document by extracting metadata and then chunking it.
        
        Args:
            content: The document content to process
            metadata: Optional pre-existing metadata
            chunking_method: Method to use for chunking
            source_type: Source type (e.g., "arxiv", "web", "pubmed")
            
        Returns:
            List of EnhancedChunkEntry objects with attached metadata
        """
        logger.info(f"Processing document with chunking method: {chunking_method}")
        
        # Step 1: Process metadata if provided, otherwise extract from content
        processed_metadata = {}
        if metadata:
            # Process the provided metadata
            processed_metadata = self.metadata_service.process_content_metadata(metadata, source_type)
        else:
            # Extract metadata using content as a source
            # For simpler cases where content is just text, create minimal metadata
            minimal_metadata = {
                "content_type": "text",
                "timestamp": self._get_timestamp(),
                "source_type": source_type or "unknown"
            }
            processed_metadata = self.metadata_service.process_content_metadata(minimal_metadata, source_type)
        
        logger.info(f"Processed metadata: {processed_metadata.get('id', 'unknown')}")
        
        # Step 2: Analyze content to determine document type if using Auto-detect
        doc_type = "unknown"
        if chunking_method == "Auto-detect" and hasattr(self.dynamic_chunker, 'content_analyzer'):
            doc_type = self.dynamic_chunker.content_analyzer.analyze(content)
            
            # Choose chunking method based on document type
            if doc_type == "technical":
                chunking_method = "Rule-based"
            elif doc_type == "conversational":
                chunking_method = "Split-based"
            else:  # mixed
                chunking_method = "LLM-based"
        
        logger.info(f"Document analyzed as: {doc_type}, using chunking method: {chunking_method}")
        
        # Step 3: Chunk the document using the appropriate method
        raw_chunks = []
        if chunking_method == "Rule-based":
            raw_chunks = self.dynamic_chunker.rule_based_chunking(content)
        elif chunking_method == "LLM-based":
            raw_chunks = self.dynamic_chunker.llm_based_chunking(content)
        else:  # Split-based (default)
            chunk_size = 1000  # Default chunk size
            raw_chunks = self.dynamic_chunker.split_document(content, chunk_size)
        
        # Step 4: Enhance chunks with rich metadata
        enhanced_chunks = []
        for i, chunk in enumerate(raw_chunks):
            # Create a copy of processed metadata for this chunk
            chunk_metadata = processed_metadata.copy()
            
            # Add chunk-specific metadata
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(raw_chunks),
                "chunk_method": chunking_method,
                "document_type": doc_type,
                "tag": chunk.metadata.get("tag", "untagged")
            })
            
            # Create enhanced chunk
            enhanced_chunk = EnhancedChunkEntry(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                content=chunk.content,
                start_index=chunk.start_index,
                end_index=chunk.end_index,
                metadata=chunk.metadata,  # Keep original metadata
                rich_metadata=chunk_metadata  # Add processed metadata
            )
            
            enhanced_chunks.append(enhanced_chunk)
        
        logger.info(f"Created {len(enhanced_chunks)} enhanced chunks with metadata")
        return enhanced_chunks
    
    def process_arxiv_paper(self, paper: Dict) -> List[EnhancedChunkEntry]:
        """
        Process an arXiv paper from the MCP client.
        
        Args:
            paper: ArXiv paper dictionary from MCP client
            
        Returns:
            List of EnhancedChunkEntry objects with attached metadata
        """
        logger.info(f"Processing arXiv paper: {paper.get('title', 'Unknown')}")
        
        # Extract the abstract for chunking
        abstract = paper.get("abstract", "")
        if not abstract or len(abstract.strip()) < 10:
            logger.warning(f"Empty or very short abstract: {paper.get('title', 'Unknown')}")
            return []
        
        # Create metadata from paper
        paper_metadata = {
            "title": paper.get("title", ""),
            "authors": paper.get("authors", []),
            "url": paper.get("url", ""),
            "publication_date": str(paper.get("year", "")),
            "categories": paper.get("categories", ""),
            "source": "arXiv",
            "source_type": "academic",
            "pdf_url": paper.get("pdf_url", "")
        }
        
        # Process the abstract with metadata
        return self.process_document(
            content=abstract,
            metadata=paper_metadata,
            chunking_method="Rule-based",  # Academic papers often work best with rule-based
            source_type="arxiv"
        )
    
    def process_pdf(self, pdf_content: str, metadata: Dict) -> List[EnhancedChunkEntry]:
        """
        Process PDF content with metadata.
        
        Args:
            pdf_content: Extracted text from PDF
            metadata: Metadata about the PDF
            
        Returns:
            List of EnhancedChunkEntry objects
        """
        logger.info(f"Processing PDF content: {metadata.get('title', 'Unknown')}")
        
        # Process with LLM-based chunking for PDFs (they often have complex structure)
        return self.process_document(
            content=pdf_content,
            metadata=metadata,
            chunking_method="LLM-based",
            source_type=metadata.get("source_type", "academic")
        )
    
    def save_chunks_to_file(self, chunks: List[EnhancedChunkEntry], output_path: str) -> str:
        """
        Save chunks to a JSON file.
        
        Args:
            chunks: List of EnhancedChunkEntry objects
            output_path: Path to save the JSON file
            
        Returns:
            Path to the saved file
        """
        import json
        from datetime import datetime
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert chunks to serializable format
        serializable_chunks = {}
        for i, chunk in enumerate(chunks):
            serializable_chunks[str(i)] = chunk.to_dict()
        
        # Add timestamp and metadata about the chunking process
        output_data = {
            "chunks": serializable_chunks,
            "metadata": {
                "timestamp": self._get_timestamp(),
                "chunk_count": len(chunks),
                "created_by": "MetadataAwareChunker"
            }
        }
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Saved {len(chunks)} chunks to {output_path}")
        return output_path
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize chunker
    metadata_aware_chunker = MetadataAwareChunker()
    
    # Test with sample content
    sample_content = """
    # Introduction to Deep Learning
    
    Deep learning is a subset of machine learning that involves neural networks with multiple layers.
    These networks can learn complex patterns in data and have revolutionized fields like computer vision and natural language processing.
    
    ## Key Concepts
    
    1. Neural Networks: Inspired by the human brain, these are the foundation of deep learning.
    2. Backpropagation: The algorithm used to train neural networks by adjusting weights.
    3. Activation Functions: Functions that determine the output of a neural network node.
    
    ## Applications
    
    Deep learning has numerous applications including:
    - Image recognition
    - Speech recognition
    - Natural language processing
    - Autonomous vehicles
    """
    
    # Sample metadata
    sample_metadata = {
        "title": "Introduction to Deep Learning",
        "authors": ["John Doe", "Jane Smith"],
        "source": "Sample Document",
        "source_type": "technical"
    }
    
    # Process the sample content
    enhanced_chunks = metadata_aware_chunker.process_document(
        content=sample_content,
        metadata=sample_metadata,
        chunking_method="Rule-based"
    )
    
    # Save chunks to file
    output_path = "output/sample_enhanced_chunks.json"
    metadata_aware_chunker.save_chunks_to_file(enhanced_chunks, output_path)
    
    print(f"✅ Created {len(enhanced_chunks)} enhanced chunks with metadata")
    print(f"✅ First chunk metadata: {enhanced_chunks[0].metadata}")
    print(f"✅ Saved to {output_path}")