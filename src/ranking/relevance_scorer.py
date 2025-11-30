import logging
from typing import List, Dict
from datetime import datetime
import re

class RelevanceScorer:
    """Scores content chunks based on relevance to query."""
    
    def __init__(self, embedder=None):
        self.logger = logging.getLogger("deep_research.ranking.relevance_scorer")
        
        # Use provided embedder or import one
        if embedder:
            self.embedder = embedder
        else:
            from src.ranking.embedder import ContentEmbedder
            self.embedder = ContentEmbedder()
    
    def score_chunks(self, query: Dict, chunks: List[Dict]) -> List[Dict]:
        """
        Score chunks based on relevance to query.
        
        Args:
            query: Dict with query text and metadata (including embedding)
            chunks: List of content chunks
            
        Returns:
            List of chunks with relevance scores added
        """
        # Get query embedding
        query_embedding = query.get("metadata", {}).get("embedding")
        if not query_embedding and "text" in query:
            # Generate embedding for query if not provided
            query_embedding = self.embedder.embed_content(query["text"])
        
        if not query_embedding:
            self.logger.error("No query embedding available")
            return chunks
        
        # Score each chunk
        scored_chunks = []
        for chunk in chunks:
            # Get or generate chunk embedding
            metadata = chunk.get("metadata", {})
            chunk_embedding = metadata.get("embedding")
            
            if not chunk_embedding and "text" in chunk:
                chunk_embedding = self.embedder.embed_content(chunk["text"])
            
            if not chunk_embedding:
                self.logger.warning(f"No embedding for chunk: {chunk.get('metadata', {}).get('chunk_id', 'unknown')}")
                # Add minimal score and continue
                metadata["relevance_score"] = 0.1
                scored_chunks.append(chunk)
                continue
            
            # Compute relevance score (semantic similarity)
            similarity = self.embedder.compute_similarity(query_embedding, chunk_embedding)
            
            # Compute quality score
            quality_score = self.assess_content_quality(chunk)
            
            # Add scores to metadata
            metadata["relevance_score"] = similarity
            metadata["quality_score"] = quality_score
            metadata["embedding"] = chunk_embedding
            
            # Create a copy with updated metadata
            scored_chunk = {
                "text": chunk.get("text", ""),
                "metadata": metadata
            }
            
            scored_chunks.append(scored_chunk)
        
        self.logger.info(f"Scored {len(scored_chunks)} chunks for relevance")
        return scored_chunks
    
    def assess_content_quality(self, chunk: Dict) -> float:
        """
        Assess content quality based on length, structure, etc.
        
        Args:
            chunk: Content chunk
            
        Returns:
            Quality score between 0 and 1
        """
        text = chunk.get("text", "")
        word_count = len(text.split())
        
        # Base score on length
        if word_count > 300:
            quality_score = 1.0  # Complete content
        elif word_count > 150:
            quality_score = 0.8  # Substantial content
        elif word_count > 75:
            quality_score = 0.6  # Medium content
        else:
            quality_score = 0.4  # Brief content
        
        # Check for indicators of quality content
        quality_indicators = [
            "introduction", "methodology", "results", "conclusion", "references",
            "abstract", "discussion", "analysis", "experiment", "findings"
        ]
        
        # Count indicators present in text
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in quality_indicators if indicator in text_lower)
        
        # Adjust score based on indicators
        if indicator_count >= 3:
            quality_score = min(1.0, quality_score + 0.2)
        elif indicator_count >= 1:
            quality_score = min(1.0, quality_score + 0.1)
        
        return quality_score
    
    def calculate_recency_score(self, chunk: Dict) -> float:
        """
        Calculate recency score based on publication date.
        
        Args:
            chunk: Content chunk
            
        Returns:
            Recency score between 0 and 1
        """
        metadata = chunk.get("metadata", {})
        
        # Get publication date
        date_str = metadata.get("publication_date")
        if not date_str:
            # Default to neutral score if no date
            return 0.5
        
        try:
            # Parse date (handle different formats)
            pub_date = None
            
            if isinstance(date_str, datetime):
                pub_date = date_str
            else:
                # Try different formats
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        pub_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
            
            if not pub_date:
                return 0.5
            
            # Calculate years from current date
            days_old = (datetime.now() - pub_date).days
            years_old = days_old / 365.0
            
            # Calculate recency score (1.0 for newest, declining with age)
            # Linear decay over 5 years
            recency = max(0.0, 1.0 - (years_old / 5.0))
            return recency
            
        except Exception as e:
            self.logger.error(f"Error calculating recency: {e}")
            return 0.5