import logging
from typing import List, Dict, Optional

class ContentSelector:
    """Orchestrates the ranking and selection of content."""
    
    def __init__(self, embedder=None, relevance_scorer=None, rank_aggregator=None):
        self.logger = logging.getLogger("deep_research.ranking.content_selector")
        
        # Initialize components (use provided ones or create new)
        if embedder:
            self.embedder = embedder
        else:
            from src.ranking.embedder import ContentEmbedder
            self.embedder = ContentEmbedder()
        
        if relevance_scorer:
            self.relevance_scorer = relevance_scorer
        else:
            from src.ranking.relevance_scorer import RelevanceScorer
            self.relevance_scorer = RelevanceScorer(self.embedder)
        
        if rank_aggregator:
            self.rank_aggregator = rank_aggregator
        else:
            from src.ranking.rank_aggregator import RankAggregator
            self.rank_aggregator = RankAggregator()
    
    def select_content(self, query: Dict, chunks: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Select the most relevant content for a query.
        
        Args:
            query: Query dictionary
            chunks: Content chunks
            top_n: Number of top chunks to return
            
        Returns:
            List of selected chunks
        """
        if not query or not chunks:
            self.logger.warning("Empty query or chunks")
            return []
        
        # Process query if needed
        if "metadata" not in query or "embedding" not in query.get("metadata", {}):
            query = self.process_query(query)
        
        # Score chunks for relevance
        self.logger.info(f"Scoring {len(chunks)} chunks for relevance")
        relevance_scored_chunks = self.relevance_scorer.score_chunks(query, chunks)
        
        # Add recency scores
        self.logger.info("Calculating recency scores")
        recency_scored_chunks = []
        for chunk in relevance_scored_chunks:
            recency_score = self.relevance_scorer.calculate_recency_score(chunk)
            # Add score to metadata
            metadata = chunk.get("metadata", {}).copy()
            metadata["recency_score"] = recency_score
            # Create new chunk with updated metadata
            recency_scored_chunks.append({
                "text": chunk.get("text", ""),
                "metadata": metadata
            })
        
        # Add authority scores
        self.logger.info("Computing authority scores")
        authority_scored_chunks = self.rank_aggregator.compute_authority_scores(recency_scored_chunks)
        
        # Calculate final scores
        self.logger.info("Calculating final scores")
        final_scored_chunks = self.rank_aggregator.calculate_final_scores(authority_scored_chunks)
        
        # Select top chunks
        self.logger.info(f"Selecting top {top_n} chunks")
        top_chunks = self.rank_aggregator.select_top_chunks(final_scored_chunks, top_n)
        
        return top_chunks
    
    def process_query(self, query: Dict) -> Dict:
        """
        Process a query to add embedding if needed.
        
        Args:
            query: Query dictionary
            
        Returns:
            Processed query with embedding
        """
        # Ensure query has the required structure
        if isinstance(query, str):
            query = {"text": query, "metadata": {}}
        elif "text" not in query:
            self.logger.error("Query missing text field")
            return query
        
        # Generate embedding if not present
        if "metadata" not in query:
            query["metadata"] = {}
        
        if "embedding" not in query["metadata"]:
            embedding = self.embedder.embed_content(query["text"])
            query["metadata"]["embedding"] = embedding
        
        return query