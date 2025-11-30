import logging
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional, Tuple
import os

logger = logging.getLogger("deep_research.ranking.visualization")

class RankingVisualizer:
    """
    Generates visualizations for ranking scores.
    """
    
    def __init__(self, output_dir="visualizations"):
        """
        Initialize visualizer.
        
        Args:
            output_dir: Directory to save visualizations
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def visualize_scores(self, chunks: List[Dict], output_file: Optional[str] = None) -> str:
        """
        Create a visualization of ranking scores.
        
        Args:
            chunks: List of content chunks with scores
            output_file: Optional filename for saved visualization
            
        Returns:
            Path to saved visualization
        """
        if not chunks:
            logger.warning("No chunks to visualize")
            return ""
            
        try:
            # Extract chunk titles and scores
            titles = []
            relevance_scores = []
            authority_scores = []
            recency_scores = []
            final_scores = []
            
            for i, chunk in enumerate(chunks):
                metadata = chunk.get("metadata", {})
                # Use truncated text or URL as title
                title = self._get_chunk_title(chunk, max_len=40)
                titles.append(f"{i+1}. {title}")
                
                # Extract scores
                relevance_scores.append(metadata.get("relevance_score", 0))
                authority_scores.append(metadata.get("authority_score", 0))
                recency_scores.append(metadata.get("recency_score", 0))
                final_scores.append(metadata.get("final_score", 0))
            
            # Create visualization
            self._create_score_chart(
                titles, 
                relevance_scores,
                authority_scores,
                recency_scores,
                final_scores,
                output_file
            )
            
            return output_file or os.path.join(self.output_dir, "ranking_scores.png")
            
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            return ""
            
    def _get_chunk_title(self, chunk: Dict, max_len: int = 40) -> str:
        """Extract a suitable title for a chunk."""
        metadata = chunk.get("metadata", {})
        
        # Try to use title from metadata if available
        if "title" in metadata:
            title = metadata["title"]
            return title[:max_len] + "..." if len(title) > max_len else title
            
        # Try to use URL from metadata
        if "url" in metadata:
            url = metadata["url"]
            # Extract domain and path
            if "/" in url:
                parts = url.split("/")
                domain = parts[2] if len(parts) > 2 else parts[0]
                path = parts[-1] if len(parts) > 3 else ""
                return f"{domain}/{path}"[:max_len]
            return url[:max_len] + "..." if len(url) > max_len else url
            
        # Use text as fallback
        text = chunk.get("text", "")
        if text:
            text = text.replace("\n", " ").strip()
            return text[:max_len] + "..." if len(text) > max_len else text
            
        # Last resort
        return f"Chunk {id(chunk) % 1000}"
        
    def _create_score_chart(
        self,
        labels: List[str],
        relevance_scores: List[float],
        authority_scores: List[float],
        recency_scores: List[float],
        final_scores: List[float],
        output_file: Optional[str] = None
    ) -> None:
        """Create a multi-score bar chart."""
        if not labels:
            return
            
        # Limit to top 10 for readability
        if len(labels) > 10:
            # Sort by final score
            sorted_indices = np.argsort(final_scores)[::-1]
            labels = [labels[i] for i in sorted_indices[:10]]
            relevance_scores = [relevance_scores[i] for i in sorted_indices[:10]]
            authority_scores = [authority_scores[i] for i in sorted_indices[:10]]
            recency_scores = [recency_scores[i] for i in sorted_indices[:10]]
            final_scores = [final_scores[i] for i in sorted_indices[:10]]
            
        # Create figure with appropriate size
        plt.figure(figsize=(12, 8))
        
        # Set up positions
        x = np.arange(len(labels))
        width = 0.2
        
        # Plot bars
        plt.bar(x - 1.5*width, relevance_scores, width, label='Relevance', color='#4285F4')
        plt.bar(x - 0.5*width, authority_scores, width, label='Authority', color='#DB4437')
        plt.bar(x + 0.5*width, recency_scores, width, label='Recency', color='#F4B400')
        plt.bar(x + 1.5*width, final_scores, width, label='Final Score', color='#0F9D58')
        
        # Configure plot
        plt.xlabel('Content Chunks')
        plt.ylabel('Score (0-1)')
        plt.title('Ranking Scores by Content Chunk')
        plt.xticks(x, labels, rotation=45, ha='right')
        plt.ylim(0, 1.1)
        plt.legend()
        plt.tight_layout()
        
        # Save or show
        if output_file:
            plt.savefig(output_file, dpi=100)
        else:
            plt.savefig(os.path.join(self.output_dir, "ranking_scores.png"), dpi=100)
            
        plt.close()
        
    def visualize_similarity_matrix(self, chunks: List[Dict], output_file: Optional[str] = None) -> str:
        """
        Create a visualization of chunk similarity matrix.
        
        Args:
            chunks: List of content chunks with embeddings
            output_file: Optional filename for saved visualization
            
        Returns:
            Path to saved visualization
        """
        if not chunks or len(chunks) < 2:
            logger.warning("Not enough chunks for similarity matrix")
            return ""
            
        try:
            # Extract embeddings if available
            embeddings = []
            titles = []
            
            for i, chunk in enumerate(chunks):
                metadata = chunk.get("metadata", {})
                embedding = metadata.get("embedding")
                
                if embedding:
                    embeddings.append(embedding)
                    titles.append(self._get_chunk_title(chunk, max_len=30))
            
            if len(embeddings) < 2:
                logger.warning("Not enough chunks have embeddings")
                return ""
                
            # Calculate similarity matrix
            similarity_matrix = np.zeros((len(embeddings), len(embeddings)))
            for i in range(len(embeddings)):
                for j in range(len(embeddings)):
                    if i == j:
                        similarity_matrix[i][j] = 1.0  # Self-similarity
                    else:
                        # Calculate cosine similarity
                        vec1 = np.array(embeddings[i])
                        vec2 = np.array(embeddings[j])
                        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                        similarity_matrix[i][j] = similarity
            
            # Plot similarity matrix
            plt.figure(figsize=(10, 8))
            plt.imshow(similarity_matrix, vmin=0, vmax=1, cmap='viridis')
            plt.colorbar(label='Cosine Similarity')
            plt.title('Content Chunk Similarity Matrix')
            
            # Add labels
            plt.xticks(np.arange(len(titles)), titles, rotation=90)
            plt.yticks(np.arange(len(titles)), titles)
            plt.tight_layout()
            
            # Save or show
            if output_file:
                plt.savefig(output_file, dpi=100)
            else:
                plt.savefig(os.path.join(self.output_dir, "similarity_matrix.png"), dpi=100)
                
            plt.close()
            
            return output_file or os.path.join(self.output_dir, "similarity_matrix.png")
            
        except Exception as e:
            logger.error(f"Error creating similarity matrix: {e}")
            return ""