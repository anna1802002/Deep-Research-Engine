"""
Chunking Service Factory

This module provides a factory for creating chunking service instances.
It allows easily switching between different chunking implementations,
including the temporary one for demos and the future official implementation
from Ticket #8.
"""

import os
import importlib
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("deep_research.chunking.factory")

# Default implementation is the temporary one
DEFAULT_CHUNKER = "src.chunking.temp_chunker.TemporaryChunker"

class ChunkerFactory:
    """
    Factory for creating chunking service instances.
    This will be used to integrate the external chunking module.
    """
    
    @staticmethod
    def create_chunker(implementation: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a chunker instance based on specified implementation.
        
        Args:
            implementation: Fully qualified class name of the chunker implementation
            config: Configuration parameters for the chunker
            
        Returns:
            Chunker instance
        """
        # Use default if not specified
        implementation = implementation or os.environ.get("CHUNKER_IMPLEMENTATION", DEFAULT_CHUNKER)
        config = config or {}
        
        try:
            # Split into module and class name
            module_path, class_name = implementation.rsplit('.', 1)
            
            # Import the module
            module = importlib.import_module(module_path)
            
            # Get the class
            chunker_class = getattr(module, class_name)
            
            # Create instance with config
            return chunker_class(**config)
            
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to create chunker '{implementation}': {e}")
            
            # Fall back to temporary chunker if different implementation failed
            if implementation != DEFAULT_CHUNKER:
                logger.info(f"Falling back to default chunker: {DEFAULT_CHUNKER}")
                return ChunkerFactory.create_chunker(DEFAULT_CHUNKER, config)
            
            # If default chunker failed, raise the exception
            raise