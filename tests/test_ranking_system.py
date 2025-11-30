import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ranking.embedder import ContentEmbedder
from src.ranking.relevance_scorer import RelevanceScorer
from src.ranking.sbert_similarity import BERTSimilarity
from src.ranking.rank_aggregator import RankAggregator
from src.ranking.content_selector import ContentSelector
from src.ranking.ranking_system import RankingSystem

class TestRankingSystem(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        # Mock the API key loading for embedder
        with patch('src.ranking.embedder.ContentEmbedder._load_api_key') as mock_load_key:
            mock_load_key.return_value = "fake-api-key"
            self.ranking_system = RankingSystem()
        
        # Sample test data (pre-chunked content)
        self.test_query = "quantum computing cryptography"
        self.test_chunks = [
            {
                "text": "Quantum computing poses significant challenges to traditional cryptography methods. "
                       "RSA and ECC may become vulnerable to Shor's algorithm when large-scale quantum computers "
                       "become available. This has led to increased research in post-quantum cryptography.",
                "metadata": {
                    "url": "https://arxiv.org/abs/quantum-crypto-123",
                    "source_type": "academic",
                    "publication_date": "2023-01-15",
                    "chunk_id": "c1",
                    "document_id": "d1"
                }
            },
            {
                "text": "Classical computers use bits as the smallest unit of data, while quantum computers use "
                       "quantum bits or qubits. This allows quantum computers to perform certain calculations "
                       "much faster than classical computers.",
                "metadata": {
                    "url": "https://example.com/quantum-basics",
                    "source_type": "web",
                    "publication_date": "2022-05-20",
                    "chunk_id": "c2",
                    "document_id": "d2"
                }
            },
            {
                "text": "Post-quantum cryptography focuses on developing encryption algorithms that are secure "
                       "against both quantum and classical computers. NIST is currently evaluating several candidate "
                       "algorithms for standardization.",
                "metadata": {
                    "url": "https://nist.gov/post-quantum",
                    "source_type": "government",
                    "publication_date": "2024-02-10",
                    "chunk_id": "c3",
                    "document_id": "d3"
                }
            }
        ]
    
    # Content chunking is tested elsewhere, as it's part of Ticket #8
    
    @patch('src.ranking.embedder.requests.post')
    def test_content_embedding(self, mock_post):
        """Test the content embedding process."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 20}]
        }
        mock_post.return_value = mock_response
        
        # Create embedder
        embedder = ContentEmbedder()
        
        # Test embedding text
        embedded = embedder.embed_content("Test content for embedding")
        
        # Should have an embedding in metadata
        self.assertEqual(1, len(embedded))
        self.assertIn("embedding", embedded[0]["metadata"])
        self.assertEqual(20, len(embedded[0]["metadata"]["embedding"]))
        
        # Test computing similarity
        similarity = embedder.compute_similarity([0.1] * 20, [0.1] * 20)
        self.assertAlmostEqual(1.0, similarity, places=5)
        
        # Test dissimilar vectors
        similarity = embedder.compute_similarity([0.1] * 20, [-0.1] * 20)
        self.assertAlmostEqual(-1.0, similarity, places=5)
    
    @patch('src.ranking.sbert_similarity.BERTSimilarity._api_similarity')
    def test_bert_similarity(self, mock_api_similarity):
        """Test BERT similarity calculation."""
        # Mock API similarity
        mock_api_similarity.return_value = 0.85
        
        # Create BERT similarity
        bert = BERTSimilarity()
        
        # Test similarity
        similarity = bert.compute_similarity(
            "Quantum computing uses qubits instead of classical bits",
            "Quantum computers leverage quantum bits for computation"
        )
        
        # Should return the mocked value
        self.assertEqual(0.85, similarity)
    
    @patch('src.ranking.embedder.ContentEmbedder._api_embedding')
    def test_relevance_scoring(self, mock_api_embedding):
        """Test relevance scoring."""
        # Mock embedding to return a simple vector
        mock_api_embedding.return_value = [0.1] * 20
        
        # Create scorer
        scorer = RelevanceScorer()
        
        # Create query and chunks
        query = {"text": "quantum computing", "metadata": {"embedding": [0.1] * 20}}
        chunks = [
            {"text": "Quantum computing article", "metadata": {"embedding": [0.1] * 20}},
            {"text": "Unrelated article", "metadata": {"embedding": [-0.1] * 20}}
        ]
        
        # Score chunks
        scored_chunks = scorer.score_chunks(query, chunks)
        
        # First chunk should have high score, second should have low score
        self.assertGreater(
            scored_chunks[0]["metadata"]["relevance_score"],
            scored_chunks[1]["metadata"]["relevance_score"]
        )
        
        # Test recency calculation
        chunk_with_date = {
            "metadata": {"publication_date": "2024-01-01"}
        }
        
        recency = scorer.calculate_recency_score(chunk_with_date)
        self.assertGreater(recency, 0.9)  # Recent content, high score
    
    def test_rank_aggregator(self):
        """Test rank aggregation."""
        # Create aggregator
        aggregator = RankAggregator()
        
        # Create test chunks with various scores
        chunks = [
            {
                "text": "Chunk 1",
                "metadata": {
                    "relevance_score": 0.9,
                    "authority_score": 0.7,
                    "recency_score": 0.8
                }
            },
            {
                "text": "Chunk 2",
                "metadata": {
                    "relevance_score": 0.6,
                    "authority_score": 0.8,
                    "recency_score": 0.9
                }
            },
            {
                "text": "Chunk 3",
                "metadata": {
                    "relevance_score": 0.3,
                    "authority_score": 0.2,
                    "recency_score": 0.1
                }
            }
        ]
        
        # Calculate final scores
        scored_chunks = aggregator.calculate_final_scores(chunks)
        
        # Should have final scores
        for chunk in scored_chunks:
            self.assertIn("final_score", chunk["metadata"])
        
        # Rank chunks
        ranked_chunks = aggregator.rank_chunks(scored_chunks)
        
        # First chunk should have highest score
        self.assertGreater(
            ranked_chunks[0]["metadata"]["final_score"],
            ranked_chunks[1]["metadata"]["final_score"]
        )
        
        # Test authority scoring
        chunks_for_authority = [
            {
                "text": "Academic content",
                "metadata": {
                    "url": "https://arxiv.org/abs/123.456",
                    "source_type": "academic"
                }
            },
            {
                "text": "Web content",
                "metadata": {
                    "url": "https://example.com/article",
                    "source_type": "web"
                }
            }
        ]
        
        authority_chunks = aggregator.compute_authority_scores(chunks_for_authority)
        
        # Academic source should have higher authority
        self.assertGreater(
            authority_chunks[0]["metadata"]["authority_score"],
            authority_chunks[1]["metadata"]["authority_score"]
        )
    
    @patch('src.ranking.content_selector.ContentSelector.process_query')
    @patch('src.ranking.content_selector.ContentSelector.select_content')
    def test_ranking_system_integration(self, mock_select, mock_process_query):
        """Test overall ranking system integration."""
        # Mock processed query
        processed_query = {"text": "test query", "metadata": {"embedding": [0.1] * 20}}
        mock_process_query.return_value = processed_query
        
        # Mock selected content
        selected_content = [
            {
                "text": "Selected content 1",
                "metadata": {
                    "relevance_score": 0.9,
                    "authority_score": 0.8,
                    "recency_score": 0.7,
                    "final_score": 0.85
                }
            }
        ]
        mock_select.return_value = selected_content
        
        # Test the full ranking process
        result = self.ranking_system.process_and_rank(
            "test query", 
            self.test_chunks,
            visualize=False
        )
        
        # Should have ranked chunks
        self.assertEqual(1, result["total_chunks"])
        self.assertEqual(selected_content, result["ranked_chunks"])

if __name__ == "__main__":
    unittest.main()