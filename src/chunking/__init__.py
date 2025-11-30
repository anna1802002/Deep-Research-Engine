"""
Chunking Module

This module provides functionality for breaking content into chunks.
It includes a temporary implementation for demo purposes, which will
be replaced by the official implementation from Ticket #8.
"""

from src.chunking.chunker_factory import ChunkerFactory
from src.chunking.chunker_interface import ChunkerInterface
from src.chunking.temp_chunker import TemporaryChunker

__all__ = ['ChunkerFactory', 'ChunkerInterface', 'TemporaryChunker']