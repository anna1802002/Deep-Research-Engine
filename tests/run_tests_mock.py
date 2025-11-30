# tests/run_tests_mock.py

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def run_tests_with_mocks():
    """Run tests with API mocking to avoid API key requirements."""
    print("🧪 Running tests with API mocks (no real API calls)")
    
    # Apply global patches for external API calls
    patches = [
        # Mock Google Custom Search
        patch('src.data_retrieval.sources.custom_search.requests.get'),
        # Mock Google Scholar
        patch('src.data_retrieval.sources.google_scholar.requests.get'),
        # Mock PubMed
        patch('src.data_retrieval.sources.pubmed.requests.get'),
        # Mock ArXiv
        patch('src.data_retrieval.sources.arxiv.requests.get'),
        # Mock Vectorizer API calls
        patch('src.query_processing.vectorizer.requests.post'),
        # Mock GROQ LLM calls
        patch('groq.Client')
    ]
    
    # Configure mock responses
    for p in patches:
        mock = p.start()
        
        # For request mocks
        if 'requests' in str(p):
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            # Different content based on the API
            if 'arxiv' in str(p):
                mock_response.text = '<feed><entry><title>Sample ArXiv Paper</title><summary>Sample summary</summary><id>http://arxiv.org/abs/sample</id></entry></feed>'
            elif 'pubmed' in str(p):
                mock_response.text = '<PubmedArticleSet><PubmedArticle><ArticleTitle>Sample PubMed Paper</ArticleTitle><AbstractText>Sample abstract</AbstractText><PMID>12345</PMID></PubmedArticle></PubmedArticleSet>'
            elif 'vectorizer' in str(p):
                mock_response.json.return_value = {"data": [{"embedding": [0.1]*1536}]}
            else:
                mock_response.json.return_value = {
                    "items": [
                        {"title": "Sample Result", "link": "https://example.com/sample", "snippet": "This is a sample search result."}
                    ]
                }
                
            mock.return_value = mock_response
        
        # For GROQ client mock
        elif 'groq' in str(p):
            mock_client = MagicMock()
            mock_chat = MagicMock()
            mock_chat.completions.create.return_value.choices = [MagicMock(message=MagicMock(content="sample, keywords, research"))]
            mock_client.chat = mock_chat
            mock.return_value = mock_client
    
    try:
        # Discover and run tests
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover('tests', pattern='test_*.py')
        
        # Run tests
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        
        # Return exit code based on test results
        exit_code = 0 if result.wasSuccessful() else 1
        
    finally:
        # Stop all patches
        for p in patches:
            p.stop()
            
    return exit_code

if __name__ == "__main__":
    sys.exit(run_tests_with_mocks())