# src/chunking_engine/chunk_metadata_connector_enhanced.py

import logging
from typing import Dict, List, Any, Union
import uuid
import hashlib
from datetime import datetime

# Import needed components
from src.metadata_processing.metadata_extractor import MetadataExtractor
from src.metadata_processing.metadata_standardizer import MetadataStandardizer
from src.metadata_processing.metadata_validator import MetadataValidator
from src.metadata_processing.metadata_integration import MetadataIntegrationService

logger = logging.getLogger("deep_research.chunking_engine.enhanced_connector")

class EnhancedChunkMetadataConnector:
    """
    Enhanced connector that integrates chunks with their metadata and ensures metadata consistency
    across the chunking process. Designed specifically to work with the MCP client.
    """
    
    def __init__(self):
        """Initialize connector with metadata processing components"""
        self.metadata_extractor = MetadataExtractor()
        self.metadata_standardizer = MetadataStandardizer()
        self.metadata_validator = MetadataValidator()
        self.metadata_service = MetadataIntegrationService()
        
        logger.info("EnhancedChunkMetadataConnector initialized")
    
    def connect_chunk_to_metadata(self, chunk: Dict, source_metadata: Dict) -> Dict:
        """
        Connect a chunk to its source metadata, ensuring the chunk has all
        necessary metadata information.
        
        Args:
            chunk: The content chunk dictionary
            source_metadata: Source document metadata
            
        Returns:
            Enhanced chunk with connected metadata
        """
        if not chunk or not source_metadata:
            logger.warning("Empty chunk or metadata provided for connection")
            return chunk
        
        try:
            # Clone the chunk to avoid modifying the original
            enhanced_chunk = chunk.copy()
            
            # Get existing metadata or create new dictionary
            chunk_metadata = enhanced_chunk.get("metadata", {}).copy()
            
            # Process metadata through standardization pipeline
            processed_metadata = self.metadata_service.process_content_metadata(
                source_metadata, 
                source_type=source_metadata.get("source_type")
            )
            
            # Add or update with processed metadata (don't overwrite existing values)
            for key, value in processed_metadata.items():
                if key not in chunk_metadata or not chunk_metadata[key]:
                    chunk_metadata[key] = value
            
            # Add unique chunk identifier if not present
            if "chunk_id" not in chunk_metadata:
                chunk_metadata["chunk_id"] = str(uuid.uuid4())
            
            # Add chunk-specific metadata
            chunk_metadata.update({
                "timestamp": datetime.now().isoformat(),
                "chunk_hash": self._generate_chunk_hash(enhanced_chunk.get("content", "")),
                "chunk_length": len(enhanced_chunk.get("content", ""))
            })
            
            # Add tag metadata if available from chunk
            if "tag" in enhanced_chunk:
                chunk_metadata["tag"] = enhanced_chunk["tag"]
                
            # Add position information if available
            if "start_index" in enhanced_chunk:
                chunk_metadata["start_index"] = enhanced_chunk["start_index"]
            if "end_index" in enhanced_chunk:
                chunk_metadata["end_index"] = enhanced_chunk["end_index"]
            
            # Update chunk with enhanced metadata
            enhanced_chunk["metadata"] = chunk_metadata
            
            return enhanced_chunk
            
        except Exception as e:
            logger.error(f"Error connecting chunk to metadata: {e}")
            return chunk
    
    def enhance_chunks_with_metadata(self, chunks: List[Dict], source_metadata: Dict) -> List[Dict]:
        """
        Enhance multiple chunks with source metadata.
        
        Args:
            chunks: List of content chunks
            source_metadata: Source document metadata
            
        Returns:
            List of enhanced chunks with connected metadata
        """
        if not chunks:
            logger.warning("No chunks provided for metadata enhancement")
            return []
        
        if not source_metadata:
            logger.warning("No source metadata provided for enhancement")
            return chunks
        
        # First validate and standardize the source metadata
        processed_metadata = self._process_source_metadata(source_metadata)
        
        # Connect each chunk to metadata
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            # Add position in sequence to metadata
            chunk_metadata = processed_metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks)
            })
            
            # Connect chunk to metadata
            enhanced_chunk = self.connect_chunk_to_metadata(chunk, chunk_metadata)
            enhanced_chunks.append(enhanced_chunk)
        
        logger.info(f"Enhanced {len(enhanced_chunks)} chunks with metadata")
        return enhanced_chunks
    
    def enhance_mcp_results(self, mcp_results: Dict) -> Dict:
        """
        Enhance MCP results by ensuring all chunks have proper metadata.
        
        Args:
            mcp_results: Results from MCP query containing chunks
            
        Returns:
            Enhanced MCP results with metadata-rich chunks
        """
        if not mcp_results:
            return {"query": "", "chunks": []}
            
        # Extract query and chunks
        query = mcp_results.get("query", "")
        chunks = mcp_results.get("chunks", [])
        
        if not chunks:
            return {"query": query, "chunks": []}
            
        # Get base metadata from the query
        base_metadata = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "source": "mcp_client",
            "source_type": "research_query"
        }
        
        # Process each chunk and enhance with metadata
        enhanced_chunks = []
        
        for chunk in chunks:
            # Extract existing metadata or create empty dict
            chunk_metadata = chunk.get("metadata", {})
            
            # Combine with base metadata
            combined_metadata = {**base_metadata, **chunk_metadata}
            
            # Enhance chunk with metadata
            enhanced_chunk = self.connect_chunk_to_metadata(chunk, combined_metadata)
            enhanced_chunks.append(enhanced_chunk)
            
        return {
            "query": query,
            "chunks": enhanced_chunks
        }
    
    def _process_source_metadata(self, metadata: Dict) -> Dict:
        """
        Process source metadata before attaching to chunks.
        Uses the metadata integration service for full processing.
        
        Args:
            metadata: Source metadata to process
            
        Returns:
            Processed metadata dictionary
        """
        try:
            # Process through metadata integration service
            processed = self.metadata_service.process_content_metadata(
                metadata, 
                source_type=metadata.get("source_type", "academic")
            )
            
            # Generate a document ID if not present
            if "id" not in processed:
                if "url" in processed:
                    processed["id"] = hashlib.md5(processed["url"].encode()).hexdigest()
                else:
                    processed["id"] = str(uuid.uuid4())
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing source metadata: {e}")
            # Return original metadata if processing fails
            return metadata
    
    def _generate_chunk_hash(self, content: str) -> str:
        """Generate a hash for chunk content"""
        if not content:
            return ""
        return hashlib.md5(content.encode()).hexdigest()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create enhanced connector
    connector = EnhancedChunkMetadataConnector()
    
    # Test with sample MCP results
    sample_mcp_results = {
        "query": "quantum computing algorithms",
        "chunks": [
            {
                "content": "Quantum computing offers exponential speedup for specific algorithms.",
                "metadata": {
                    "source": "arxiv",
                    "title": "Advances in Quantum Algorithms"
                }
            },
            {
                "content": "Shor's algorithm can factor large numbers efficiently on quantum computers.",
                "metadata": {
                    "source": "academic_paper",
                    "publication_date": "2023-01-15"
                }
            }
        ]
    }
    
    # Enhance the MCP results
    enhanced_results = connector.enhance_mcp_results(sample_mcp_results)
    
    print("\n✅ Enhanced MCP Results:")
    print(f"Query: {enhanced_results['query']}")
    print(f"Number of chunks: {len(enhanced_results['chunks'])}")
    
    # Print the first chunk's metadata to verify enhancement
    if enhanced_results["chunks"]:
        first_chunk = enhanced_results["chunks"][0]
        print("\n✅ First chunk metadata:")
        for key, value in first_chunk["metadata"].items():
            print(f"  {key}: {value}")