import os
import sys
import pytest
from unittest.mock import Mock, call
from datetime import datetime
import uuid
import hashlib

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.metadata_processing.metadata_processor import MetadataProcessor
from src.database.vector_store import ChromaDBManager

class TestMetadataProcessor:
    def setup_method(self):
        # Create a mock ChromaDB manager to avoid actual database interactions
        self.mock_chroma_manager = Mock(spec=ChromaDBManager)
        self.processor = MetadataProcessor(self.mock_chroma_manager)
    
    def test_store_processed_metadata_with_url(self):
        metadata = {
            "title": "Test Paper",
            "url": "https://example.com/paper",
            "source": "Web"
        }
        
        # Store metadata
        stored_id = self.processor.store_processed_metadata(metadata)
        
        # Verify URL-based ID generation
        expected_id = hashlib.md5(metadata["url"].encode()).hexdigest()
        assert stored_id == expected_id
        
        # Verify store_embedding was called once
        self.mock_chroma_manager.store_embedding.assert_called_once()
        
        # Get the call arguments 
        store_call = self.mock_chroma_manager.store_embedding.call_args
        
        # Unpack the positional arguments
        call_args = store_call[0]
        
        # Check collection name
        assert call_args[0] == "metadata_collection"
        
        # Check ID matches expected
        assert call_args[1] == expected_id
        
        # Verify stored metadata
        stored_metadata = store_call[1]['metadata']
        assert 'timestamp' in stored_metadata
        
        # Optional: Additional checks on stored metadata
        assert stored_metadata['title'] == "Test Paper"
        assert stored_metadata['url'] == "https://example.com/paper"
        assert stored_metadata['source'] == "Web"
    
    def test_store_processed_metadata_without_url(self):
        metadata = {
            "title": "Test Paper without URL",
            "source": "Manual"
        }
        
        # Store metadata
        stored_id = self.processor.store_processed_metadata(metadata)
        
        # Verify UUID-based ID generation
        assert uuid.UUID(stored_id)  # Validate it's a valid UUID
        
        # Verify store_embedding was called
        self.mock_chroma_manager.store_embedding.assert_called_once()

# Ensure the test can be run directly
if __name__ == "__main__":
    pytest.main([__file__])