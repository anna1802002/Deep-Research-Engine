"""
Chunking Interface

This module defines the interface that all chunking implementations should follow.
This ensures that different implementations can be easily swapped without changing
the rest of the codebase.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ChunkerInterface(ABC):
    """
    Interface for content chunking services.
    This interface will be implemented by the external chunking module.
    """
    
    @abstractmethod
    def create_chunks(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split content into chunks with metadata.
        
        Args:
            content: Dictionary containing text and metadata
            
        Returns:
            List of chunks with text and metadata
        """
        pass