import logging
import os
import time
from typing import Dict, List, Optional, Union
import yaml

class RankingSystem:
    """Main API for the content ranking pipeline."""
    
    def __init__(self, config_path="config/settings.yaml"):
        self.logger = logging.getLogger("deep_research.ranking.system")
        self.config = self._load_config(config_path)
        
        # Initialize components
        from src.ranking.embedder import ContentEmbedder
        from src.ranking.relevance_scorer import RelevanceScorer
        from src.ranking.rank_aggregator import RankAggregator
        from src.ranking.content_selector import ContentSelector
        
        # Create embedder with configured model
        self.embedder = ContentEmbedder(
            model_name=self.config.get("model", "all-MiniLM-L6-v2")
        )
        
        # Create ranking components
        self.relevance_scorer = RelevanceScorer(self.embedder)
        self.rank_aggregator = RankAggregator()
        self.content_selector = ContentSelector(
            embedder=self.embedder,
            relevance_scorer=self.relevance_scorer,
            rank_aggregator=self.rank_aggregator
        )
        
        # Metrics
        self.metrics = {
            "total_queries": 0,
            "total_chunks": 0,
            "average_time": 0
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from settings file."""
        default_config = {
            "model": "all-MiniLM-L6-v2",
            "top_n": 10
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as file:
                    config = yaml.safe_load(file)
                    ranking_config = config.get("ranking", {})
                    
                    # Use defaults for missing values
                    for key, value in default_config.items():
                        if key not in ranking_config:
                            ranking_config[key] = value
                            
                    return ranking_config
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            
        return default_config
    
    def process_query(self, query_text: str) -> Dict:
        """
        Process and prepare a query for content ranking.
        
        Args:
            query_text: Raw query text
            
        Returns:
            Query dictionary with embedding
        """
        self.logger.info(f"Processing query: {query_text}")
        
        query = {"text": query_text, "metadata": {}}
        
        try:
            # Generate embedding
            embedding = self.embedder.embed_content(query_text)
            query["metadata"]["embedding"] = embedding
            self.logger.info("Query embedded successfully")
        except Exception as e:
            self.logger.error(f"Error embedding query: {e}")
            
        return query
    
    def rank_content(self, query: Union[str, Dict], chunks: List[Dict], top_n: Optional[int] = None) -> List[Dict]:
        """
        Rank content chunks based on relevance to query.
        
        Args:
            query: Query text or dictionary
            chunks: Content chunks
            top_n: Number of top results to return
            
        Returns:
            Ranked list of chunks
        """
        start_time = time.time()
        
        # Process query if it's just text
        if isinstance(query, str):
            query = self.process_query(query)
        
        # Use default top_n if not specified
        if top_n is None:
            top_n = self.config.get("top_n", 10)
        
        self.logger.info(f"Ranking {len(chunks)} chunks")
        
        try:
            # Select content
            ranked_chunks = self.content_selector.select_content(query, chunks, top_n)
            
            # Update metrics
            self.metrics["total_queries"] += 1
            self.metrics["total_chunks"] += len(chunks)
            
            elapsed_time = time.time() - start_time
            
            # Update average time with exponential moving average
            if self.metrics["average_time"] == 0:
                self.metrics["average_time"] = elapsed_time
            else:
                self.metrics["average_time"] = (
                    0.9 * self.metrics["average_time"] + 0.1 * elapsed_time
                )
                
            self.logger.info(f"Ranked {len(chunks)} chunks in {elapsed_time:.2f}s")
            
            return ranked_chunks
            
        except Exception as e:
            self.logger.error(f"Error ranking content: {e}")
            return []
    
    def process_and_rank(self, query: Union[str, Dict], chunks: List[Dict], top_n: Optional[int] = None, visualize: bool = False) -> Dict:
        """
        Complete ranking pipeline in one function.
        
        Args:
            query: Query text or dictionary
            chunks: Content chunks
            top_n: Number of top results to return
            visualize: Whether to create visualizations
            
        Returns:
            Dictionary with ranked chunks and metadata
        """
        # Process query if needed
        if isinstance(query, str):
            query = self.process_query(query)
        
        # Rank content
        ranked_chunks = self.rank_content(query, chunks, top_n)
        
        # Create result dictionary
        result = {
            "ranked_chunks": ranked_chunks,
            "total_chunks": len(ranked_chunks),
            "processing_time": f"{self.metrics['average_time']:.2f}s"
        }
        
        return result