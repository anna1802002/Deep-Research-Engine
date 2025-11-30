# src/metadata_processing/metadata_integration.py
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Import metadata processing components
from .metadata_extractor import MetadataExtractor
from .metadata_standardizer import MetadataStandardizer
from .metadata_validator import MetadataValidator
from .metadata_processor import MetadataProcessor
from .standardization import StandardizationService

logger = logging.getLogger("deep_research.metadata_processing.integration")

class MetadataIntegrationService:
    """
    Service that integrates metadata processing with chunking system.
    Provides unified interfaces for the chunking pipeline to process metadata.
    """
    
    def __init__(self):
        """Initialize integration service components."""
        self.extractor = MetadataExtractor()
        self.standardizer = MetadataStandardizer()
        self.validator = MetadataValidator()
        self.processor = MetadataProcessor()
        self.standardization_service = StandardizationService()
        
    def process_content_metadata(self, content: Dict, source_type: str = None) -> Dict:
        """
        Process content metadata through the complete pipeline:
        1. Extract metadata based on source type
        2. Standardize field names
        3. Validate completeness
        4. Process and prepare for storage
        
        Args:
            content: Content dictionary with potential metadata
            source_type: Source type (e.g., "arxiv", "web", "pubmed")
            
        Returns:
            Processed metadata dictionary
        """
        try:
            logger.info(f"Processing metadata for content from source type: {source_type}")
            
            # Extract metadata
            raw_metadata = content.get("metadata", {})
            if not raw_metadata:
                logger.warning("No metadata found in content, using content as source")
                raw_metadata = content
                
            extracted = self.extractor.extract_metadata(raw_metadata, source_type)
            
            # Standardize
            standardized = self.standardizer.standardize_metadata([extracted])[0]
            
            # Validate
            validated = self.validator.validate(standardized)
            
            # Process for storage
            processed = self.processor.process_metadata(validated)
            
            logger.info(f"Metadata processing complete with ID: {processed.get('id')}")
            return processed
            
        except Exception as e:
            logger.error(f"Error processing content metadata: {e}")
            # Return minimal metadata to prevent failures
            return {
                "title": content.get("title", "Unknown"),
                "source": source_type or "Unknown",
                "timestamp": datetime.now().isoformat(),
                "id": "error_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                "_processing_error": str(e)
            }
    
    def enrich_chunks_with_metadata(self, chunks: List[Dict], metadata: Dict) -> List[Dict]:
        """
        Attach metadata to content chunks.
        
        Args:
            chunks: List of content chunks
            metadata: Metadata to attach to chunks
            
        Returns:
            List of chunks with attached metadata
        """
        try:
            # Process chunk metadata via processor
            return self.processor.attach_metadata_to_chunks(chunks, metadata)
        except Exception as e:
            logger.error(f"Error enriching chunks with metadata: {e}")
            # Apply minimal metadata to chunks
            return [
                {**chunk, "metadata": {**(chunk.get("metadata", {})), "error": str(e)}}
                for chunk in chunks
            ]
    
    def process_document_with_chunking(self, document_content: Dict, chunker=None) -> Dict:
        """
        Process document content and create chunks with metadata.
        
        Args:
            document_content: Document content dictionary
            chunker: Optional chunker instance
            
        Returns:
            Processed document with chunks and metadata
        """
        try:
            # Process document metadata
            source_type = document_content.get("source_type", None)
            processed_metadata = self.process_content_metadata(document_content, source_type)
            
            # If chunker is provided, create chunks
            chunks = []
            if chunker and "text" in document_content:
                # Use the provided chunker to create chunks
                text = document_content["text"]
                chunks = chunker.split_document(text, chunk_size=1000)  # Use default chunk size
                
                # Convert chunks to dictionary format if needed
                if hasattr(chunks[0], "__dict__"):
                    chunks = [vars(chunk) for chunk in chunks]
                    
                logger.info(f"Created {len(chunks)} chunks using provided chunker")
            elif "chunks" in document_content:
                # Use existing chunks
                chunks = document_content["chunks"]
                logger.info(f"Using {len(chunks)} existing chunks from document")
            
            # Attach metadata to chunks
            if chunks:
                enriched_chunks = self.enrich_chunks_with_metadata(chunks, processed_metadata)
                
                # Return processed document
                return {
                    "text": document_content.get("text", ""),
                    "metadata": processed_metadata,
                    "chunks": enriched_chunks
                }
            else:
                logger.warning("No chunks created or found in document")
                return {
                    "text": document_content.get("text", ""),
                    "metadata": processed_metadata,
                    "chunks": []
                }
                
        except Exception as e:
            logger.error(f"Error processing document with chunking: {e}")
            return {
                "text": document_content.get("text", ""),
                "metadata": {"error": str(e)},
                "chunks": []
            }
    
    def process_arxiv_result(self, arxiv_paper: Dict) -> Dict:
        """
        Process ArXiv paper result from MCP client.
        
        Args:
            arxiv_paper: ArXiv paper dictionary from MCP client
            
        Returns:
            Processed paper with metadata
        """
        # Extract basic fields
        paper_content = {
            "text": arxiv_paper.get("abstract", ""),
            "metadata": {
                "title": arxiv_paper.get("title", ""),
                "authors": arxiv_paper.get("authors", []),
                "url": arxiv_paper.get("url", ""),
                "publication_date": str(arxiv_paper.get("year", "")),
                "categories": arxiv_paper.get("categories", ""),
                "source": "arXiv",
                "source_type": "academic",
                "pdf_url": arxiv_paper.get("pdf_url", "")
            }
        }
        
        # Process through metadata pipeline
        return self.process_document_with_chunking(paper_content)
    
    def integrate_with_mcp_client(self, query_results: Dict) -> Dict:
        """
        Integrate with MCP client results.
        
        Args:
            query_results: Query results from MCP client
            
        Returns:
            Processed results with enriched metadata
        """
        if not query_results:
            logger.warning("Empty query results provided for integration")
            return {"query": "", "chunks": []}
            
        query = query_results.get("query", "")
        chunks = query_results.get("chunks", [])
        
        # Process each chunk's metadata
        processed_chunks = []
        for chunk in chunks:
            # Extract existing metadata
            chunk_metadata = chunk.get("metadata", {})
            
            # Process metadata
            processed_metadata = self.process_content_metadata(chunk, chunk_metadata.get("source_type"))
            
            # Update chunk with processed metadata
            processed_chunk = chunk.copy()
            processed_chunk["metadata"] = processed_metadata
            processed_chunks.append(processed_chunk)
        
        logger.info(f"Processed metadata for {len(processed_chunks)} chunks from MCP client")
        return {"query": query, "chunks": processed_chunks}
    
    def save_processed_metadata(self, metadata: Dict, output_file: str = None) -> None:
        """
        Save processed metadata to file.
        
        Args:
            metadata: Processed metadata dictionary
            output_file: Output file path (optional)
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"processed_metadata_{timestamp}.json"
            
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved processed metadata to {output_file}")
        except Exception as e:
            logger.error(f"Error saving processed metadata: {e}")

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    integration = MetadataIntegrationService()
    
    # Test with sample ArXiv paper
    sample_paper = {
        "title": "Deep Learning for Natural Language Processing",
        "authors": ["John Smith", "Jane Doe"],
        "year": "2023",
        "url": "https://arxiv.org/abs/2305.12345",
        "categories": "cs.CL, cs.AI",
        "abstract": "This paper explores deep learning techniques for NLP tasks."
    }
    
    processed = integration.process_arxiv_result(sample_paper)
    print(json.dumps(processed, indent=2))