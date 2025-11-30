import logging
from typing import List, Dict
import yaml
import os

class RankAggregator:
    """Combines multiple ranking signals into final score."""
    
    def __init__(self, config_path="config/settings.yaml"):
        self.logger = logging.getLogger("deep_research.ranking.rank_aggregator")
        self.weights = self._load_weights(config_path)
    
    def _load_weights(self, config_path: str) -> Dict[str, float]:
        """Load ranking weights from settings."""
        # Default weights
        default_weights = {
            "semantic": 0.5,  # Semantic relevance
            "authority": 0.3,  # Source authority
            "recency": 0.2    # Content recency
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as file:
                    config = yaml.safe_load(file)
                    ranking_config = config.get("ranking", {})
                    
                    weights = {
                        "semantic": ranking_config.get("weight_semantic", default_weights["semantic"]),
                        "authority": ranking_config.get("weight_authority", default_weights["authority"]),
                        "recency": ranking_config.get("weight_recency", default_weights["recency"])
                    }
                    
                    # Normalize weights to sum to 1
                    total = sum(weights.values())
                    if total > 0:
                        weights = {k: v/total for k, v in weights.items()}
                        
                    return weights
        except Exception as e:
            self.logger.error(f"Error loading weights: {e}")
        
        return default_weights
    
    def calculate_final_scores(self, chunks: List[Dict]) -> List[Dict]:
        """
        Calculate final ranking scores by combining all signals.
        
        Args:
            chunks: Content chunks with individual scores
            
        Returns:
            Chunks with final scores added
        """
        if not chunks:
            return []
        
        result_chunks = []
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            
            # Get individual scores with defaults
            relevance = metadata.get("relevance_score", 0.5)  # Semantic relevance
            authority = metadata.get("authority_score", 0.5)  # Source authority
            recency = metadata.get("recency_score", 0.5)      # Content recency
            quality = metadata.get("quality_score", 0.5)      # Content quality
            
            # Calculate weighted sum
            final_score = (
                (relevance * self.weights["semantic"]) +
                (authority * self.weights["authority"]) +
                (recency * self.weights["recency"]) +
                (quality * 0.1)  # Quality always has small weight
            ) / (sum(self.weights.values()) + 0.1)  # Normalize
            
            # Add to metadata
            metadata["final_score"] = final_score
            
            # Create copy with updated metadata
            result_chunk = {
                "text": chunk.get("text", ""),
                "metadata": metadata
            }
            
            result_chunks.append(result_chunk)
        
        self.logger.info(f"Calculated final scores for {len(result_chunks)} chunks")
        return result_chunks
    
    def rank_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Sort chunks by final score (highest first).
        
        Args:
            chunks: Content chunks with final scores
            
        Returns:
            Ranked list of chunks
        """
        # Sort by final score (descending)
        return sorted(
            chunks,
            key=lambda x: x.get("metadata", {}).get("final_score", 0),
            reverse=True
        )
    
    def select_top_chunks(self, chunks: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Select top N ranked chunks.
        
        Args:
            chunks: Content chunks
            top_n: Number of top chunks to select
            
        Returns:
            Top N chunks
        """
        ranked_chunks = self.rank_chunks(chunks)
        return ranked_chunks[:top_n]
    
    def compute_authority_scores(self, chunks: List[Dict]) -> List[Dict]:
        """
        Compute authority scores based on source credibility.
        
        Args:
            chunks: Content chunks
            
        Returns:
            Chunks with authority scores added
        """
        # Domain authority scores
        domain_scores = {
            "arxiv.org": 0.85,
            "scholar.google.com": 0.80,
            "pubmed.ncbi.nlm.nih.gov": 0.90,
            "nature.com": 0.95,
            "science.org": 0.95,
            "ieee.org": 0.85,
            "acm.org": 0.85,
            "nih.gov": 0.90,
            "edu": 0.80,
            "gov": 0.85,
            "org": 0.75,
            "com": 0.60
        }
        
        result_chunks = []
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            url = metadata.get("url", "")
            
            # Calculate authority score
            authority_score = 0.5  # Default
            
            # Extract domain from URL
            import re
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            domain = domain_match.group(1) if domain_match else ""
            
            # Check for exact match
            if domain in domain_scores:
                authority_score = domain_scores[domain]
            else:
                # Check for partial match
                for d, score in domain_scores.items():
                    if domain.endswith(f".{d}"):
                        authority_score = score * 0.9  # Slightly lower for partial match
                        break
            
            # Adjust based on source type
            source_type = metadata.get("source_type", "")
            if source_type == "academic":
                authority_score = min(1.0, authority_score * 1.1)  # Boost academic sources
            
            # Add to metadata
            metadata["authority_score"] = authority_score
            
            # Create copy with updated metadata
            result_chunk = {
                "text": chunk.get("text", ""),
                "metadata": metadata
            }
            
            result_chunks.append(result_chunk)
        
        self.logger.info(f"Computed authority scores for {len(result_chunks)} chunks")
        return result_chunks