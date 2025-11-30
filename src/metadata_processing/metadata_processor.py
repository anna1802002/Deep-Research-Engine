# src/metadata_processing/metadata_processor.py
import hashlib
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger("deep_research.metadata_processing.processor")

class MetadataProcessor:
    """
    Processes, stores, and retrieves metadata with appropriate embeddings.
    Ensures metadata is properly attached to content chunks.
    """
    
    def __init__(self, embedding_service=None, storage_service=None):
        """
        Initialize MetadataProcessor with optional embedding and storage services.
        
        Args:
            embedding_service: Service to generate embeddings (optional)
            storage_service: Service to store metadata (optional)
        """
        self.embedding_service = embedding_service
        self.storage_service = storage_service
        
        try:
            # Try to import ChromaDB manager if available
            from src.database.vector_store import ChromaDBManager
            self.chroma_manager = ChromaDBManager()
            logger.info("ChromaDB manager initialized for metadata storage")
        except ImportError:
            logger.warning("ChromaDBManager not available, vector storage disabled")
            self.chroma_manager = None
    
    def process_metadata(self, metadata: Dict) -> Dict:
        """
        Process raw metadata by cleaning, validating and enhancing it.
        
        Args:
            metadata: Raw metadata dictionary
            
        Returns:
            Processed metadata with additional fields
        """
        if not metadata:
            logger.warning("Empty metadata provided for processing")
            return {}
            
        # Make a copy to avoid modifying original
        processed = metadata.copy()
        
        # Generate ID based on URL or title+source, or fallback to UUID
        if "url" in processed and processed["url"]:
            processed["id"] = hashlib.md5(processed["url"].encode()).hexdigest()
        elif "title" in processed and "source" in processed:
            id_str = f"{processed['title']}_{processed['source']}"
            processed["id"] = hashlib.md5(id_str.encode()).hexdigest()
        else:
            processed["id"] = str(uuid.uuid4())
        
        # Add timestamp if not present
        if "timestamp" not in processed:
            processed["timestamp"] = datetime.now().isoformat()
            
        # Add processing info
        processed["_processing"] = {
            "processor_version": "1.0",
            "processing_date": datetime.now().isoformat()
        }
        
        # Ensure source_type is set
        if "source_type" not in processed:
            # Try to infer from source
            source = processed.get("source", "").lower()
            if source in ["arxiv", "pubmed", "journal", "ieee", "acm"]:
                processed["source_type"] = "academic"
            else:
                processed["source_type"] = "unknown"
        
        logger.info(f"Processed metadata with ID: {processed['id']}")
        return processed
    
    def store_processed_metadata(self, metadata: Dict) -> Optional[str]:
        """
        Store processed metadata with embedding into vector store.
        
        Args:
            metadata: Processed metadata dictionary
            
        Returns:
            ID of stored metadata or None on failure
        """
        if not metadata:
            logger.warning("Empty metadata provided for storage")
            return None
            
        # Get ID from metadata or generate new one
        if "id" in metadata:
            id = metadata["id"]
        elif "url" in metadata:
            id = hashlib.md5(metadata["url"].encode()).hexdigest()
        else:
            id = str(uuid.uuid4())
            
        # If storage service is available, use it
        if self.storage_service:
            try:
                return self.storage_service.store(metadata, id)
            except Exception as e:
                logger.error(f"Error storing metadata with storage service: {e}")
        
        # Otherwise, try to use ChromaDB manager directly
        if self.chroma_manager:
            try:
                # Generate embedding if embedding service is available
                embedding = None
                if self.embedding_service:
                    try:
                        # Convert metadata to string for embedding
                        metadata_text = f"{metadata.get('title', '')} {metadata.get('abstract', '')}"
                        embedding = self.embedding_service.get_embedding(metadata_text)
                    except Exception as e:
                        logger.error(f"Error generating embedding: {e}")
                
                # Use placeholder embedding if real embedding not available
                if not embedding:
                    embedding = [0.0] * 768  # Standard size for many embedding models
                
                # Store in ChromaDB
                self.chroma_manager.store_embedding(
                    collection_name="metadata_collection", 
                    id=id, 
                    text=str(metadata), 
                    embedding=embedding,
                    metadata=metadata
                )
                logger.info(f"Stored metadata in ChromaDB with ID: {id}")
                return id
            except Exception as e:
                logger.error(f"Error storing metadata in ChromaDB: {e}")
        
        logger.warning("No storage method available for metadata")
        return None
        
    def attach_metadata_to_chunks(self, chunks: List[Dict], metadata: Dict) -> List[Dict]:
        """
        Attach appropriate metadata to each content chunk.
        
        Args:
            chunks: List of content chunk dictionaries
            metadata: Metadata to attach to chunks
            
        Returns:
            List of chunks with attached metadata
        """
        if not chunks:
            logger.warning("No chunks provided for metadata attachment")
            return []
            
        if not metadata:
            logger.warning("No metadata provided for chunk attachment")
            return chunks
            
        enriched_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Make a copy of the chunk to avoid modifying original
            enriched_chunk = chunk.copy()
            
            # If chunk already has metadata, merge with provided metadata
            if "metadata" in enriched_chunk and enriched_chunk["metadata"]:
                # Make a copy of the chunk metadata
                chunk_metadata = enriched_chunk["metadata"].copy()
                
                # Add or update with metadata fields, but don't overwrite existing values
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
            
        logger.info(f"Attached metadata to {len(enriched_chunks)} chunks")
        return enriched_chunks
        
    def process_document(self, document: Dict) -> Dict:
        """
        Process a complete document, including its metadata and chunks.
        
        Args:
            document: Document dictionary with text, metadata, and chunks
            
        Returns:
            Processed document with enhanced metadata
        """
        if not document:
            logger.warning("Empty document provided for processing")
            return {}
            
        try:
            # Process metadata
            metadata = document.get("metadata", {})
            processed_metadata = self.process_metadata(metadata)
            
            # Update document metadata
            document["metadata"] = processed_metadata
            
            # Process chunks if they exist
            if "chunks" in document and document["chunks"]:
                document["chunks"] = self.attach_metadata_to_chunks(
                    document["chunks"], 
                    processed_metadata
                )
                
            # Store metadata if storage is available
            if processed_metadata and (self.storage_service or self.chroma_manager):
                self.store_processed_metadata(processed_metadata)
                
            logger.info("Document processed successfully with metadata enhancement")
            return document
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return document  # Return original on error

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create processor
    processor = MetadataProcessor()
    
    # Test with sample data
    sample_metadata = {
        "title": "Example Research Paper",
        "authors": ["John Doe", "Jane Smith"],
        "source": "ArXiv",
        "url": "https://example.com/paper123"
    }
    
    processed_metadata = processor.process_metadata(sample_metadata)
    print("\n✅ Processed Metadata:")
    print(processed_metadata)
    
    # Test with sample document
    sample_document = {
        "text": "This is the full text of the document.",
        "metadata": sample_metadata,
        "chunks": [
            {"text": "This is chunk 1"},
            {"text": "This is chunk 2", "metadata": {"existing": "value"}}
        ]
    }
    
    processed_document = processor.process_document(sample_document)
    print("\n✅ Processed Document:")
    print(f"Document metadata: {processed_document['metadata']}")
    print(f"Number of chunks: {len(processed_document['chunks'])}")
    print(f"First chunk metadata: {processed_document['chunks'][0]['metadata']}")