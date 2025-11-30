# src/metadata_processing/standardization.py
from typing import Dict, List, Any, Union
import logging
from .metadata_standardizer import MetadataStandardizer
from .citation_extractor import CitationExtractor

logger = logging.getLogger("deep_research.metadata_processing.standardization")

class StandardizationService:
    """
    Service that handles all standardization operations for metadata and citations.
    Provides a unified interface for the standardization pipeline.
    """
    
    def __init__(self):
        """Initialize standardization components."""
        self.metadata_standardizer = MetadataStandardizer()
        self.citation_extractor = CitationExtractor()
        
    def standardize_metadata(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        Standardize a list of metadata entries.
        
        Args:
            metadata_list: List of metadata dictionaries to standardize
            
        Returns:
            List of standardized metadata dictionaries
        """
        if not metadata_list:
            logger.warning("Empty metadata list provided for standardization")
            return []
            
        try:
            logger.info(f"Standardizing {len(metadata_list)} metadata entries")
            return self.metadata_standardizer.standardize_metadata(metadata_list)
        except Exception as e:
            logger.error(f"Error standardizing metadata: {e}")
            return metadata_list  # Return original on error
            
    def extract_citations(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        Extract citations from metadata entries.
        
        Args:
            metadata_list: List of metadata dictionaries
            
        Returns:
            List of extracted citation dictionaries
        """
        if not metadata_list:
            logger.warning("Empty metadata list provided for citation extraction")
            return []
            
        try:
            logger.info(f"Extracting citations from {len(metadata_list)} metadata entries")
            return self.citation_extractor.extract_citations(metadata_list)
        except Exception as e:
            logger.error(f"Error extracting citations: {e}")
            return []
            
    def enrich_chunks_with_metadata(self, chunks: List[Dict], metadata: Dict) -> List[Dict]:
        """
        Attach appropriate metadata to each chunk.
        
        Args:
            chunks: List of content chunks
            metadata: Metadata dictionary to attach to chunks
            
        Returns:
            List of chunks with attached metadata
        """
        if not chunks:
            logger.warning("No chunks provided for metadata enrichment")
            return []
            
        enriched_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Create a copy of the chunk to avoid modifying the original
            enriched_chunk = chunk.copy()
            
            # If chunk already has metadata, merge with provided metadata
            if "metadata" in enriched_chunk and enriched_chunk["metadata"]:
                # Create a copy of the metadata to avoid modifying the original
                chunk_metadata = enriched_chunk["metadata"].copy()
                
                # Update with new metadata, but keep existing values if they exist
                for key, value in metadata.items():
                    if key not in chunk_metadata or not chunk_metadata[key]:
                        chunk_metadata[key] = value
                        
                # Add chunk-specific metadata
                chunk_metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
                
                enriched_chunk["metadata"] = chunk_metadata
            else:
                # Create new metadata dict with chunk-specific info
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
                
                enriched_chunk["metadata"] = chunk_metadata
                
            enriched_chunks.append(enriched_chunk)
            
        logger.info(f"Enriched {len(enriched_chunks)} chunks with metadata")
        return enriched_chunks
        
    def process_document_with_metadata(self, document: Dict) -> Dict:
        """
        Process a complete document with its metadata and chunks.
        
        Args:
            document: Dictionary containing text, metadata, and possibly chunks
            
        Returns:
            Processed document with standardized metadata attached to chunks
        """
        if not document:
            logger.warning("Empty document provided for processing")
            return {}
            
        try:
            # Extract and standardize base metadata
            metadata = document.get("metadata", {})
            standardized_metadata = self.metadata_standardizer.standardize_metadata([metadata])
            
            if standardized_metadata:
                processed_metadata = standardized_metadata[0]
            else:
                processed_metadata = metadata
                
            # Update the document's metadata
            document["metadata"] = processed_metadata
            
            # Process chunks if they exist
            if "chunks" in document and document["chunks"]:
                document["chunks"] = self.enrich_chunks_with_metadata(
                    document["chunks"], 
                    processed_metadata
                )
                
            logger.info("Document processed successfully with metadata standardization")
            return document
            
        except Exception as e:
            logger.error(f"Error processing document with metadata: {e}")
            return document  # Return original on error

# Example usage when run directly
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample data
    standardization_service = StandardizationService()
    
    sample_metadata = [
        {"Title": "AI in Medicine", "Authors": "John Doe, Jane Smith", "DOI": "https://doi.org/10.1234/aimed"},
        {"title": "Deep Learning", "author": ["Alice Brown", "Bob White"], "doi": "10.5678/dl"}
    ]
    
    standardized = standardization_service.standardize_metadata(sample_metadata)
    print("\n✅ Standardized Metadata:")
    for entry in standardized:
        print(entry)
        
    # Test citation extraction
    citations = standardization_service.extract_citations(standardized)
    print("\n✅ Extracted Citations:")
    for citation in citations:
        print(citation)
        
    # Test chunk enrichment
    sample_chunks = [
        {"text": "This is chunk 1"},
        {"text": "This is chunk 2", "metadata": {"existing": "value"}}
    ]
    
    sample_doc_metadata = {
        "title": "Sample Document",
        "authors": ["Test Author"],
        "source": "Test Source",
        "url": "https://example.com"
    }
    
    enriched_chunks = standardization_service.enrich_chunks_with_metadata(sample_chunks, sample_doc_metadata)
    print("\n✅ Enriched Chunks:")
    for chunk in enriched_chunks:
        print(chunk)