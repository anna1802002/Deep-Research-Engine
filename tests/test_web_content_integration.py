# tests/test_web_content_integration.py

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_retrieval.web_fetcher import WebFetcher
from src.data_retrieval.content_processor import ContentProcessor
from src.data_retrieval.sources.custom_search import CustomSearchClient

class TestWebContentIntegration(unittest.TestCase):
    
    @patch('src.data_retrieval.sources.custom_search.CustomSearchClient.search')
    @patch('src.data_retrieval.web_fetcher.WebFetcher.fetch_url')
    def test_search_and_process_workflow(self, mock_fetch_url, mock_search):
        """Test the complete workflow from search to content processing"""
        
        # Mock search results
        mock_search.return_value = [
            {"title": "Test Result 1", "url": "https://example.com/result1", "snippet": "Test snippet 1"},
            {"title": "Test Result 2", "url": "https://example.com/result2", "snippet": "Test snippet 2"}
        ]
        
        # Mock fetch results
        mock_fetch_url.side_effect = [
            {
                "text": "Processed content for result 1",
                "metadata": {
                    "url": "https://example.com/result1",
                    "content_type": "text",
                    "subtype": "html"
                }
            },
            {
                "text": "Processed content for result 2",
                "metadata": {
                    "url": "https://example.com/result2",
                    "content_type": "text",
                    "subtype": "html"
                }
            }
        ]
        
        # Initialize components
        search_client = CustomSearchClient()
        fetcher = WebFetcher()
        
        # Run the workflow
        query = "test query"
        search_results = search_client.search(query, max_results=2)
        
        # Verify search results
        self.assertEqual(2, len(search_results))
        self.assertEqual("Test Result 1", search_results[0]["title"])
        
        # Extract URLs for fetching
        urls = [result["url"] for result in search_results]
        
        # Fetch and process content
        processed_results = []
        for url in urls:
            processed = fetcher.fetch_url(url)
            if processed:
                processed_results.append(processed)
        
        # Verify processed results
        self.assertEqual(2, len(processed_results))
        self.assertEqual("Processed content for result 1", processed_results[0]["text"])
        self.assertEqual("Processed content for result 2", processed_results[1]["text"])
        
    @patch('requests.get')
    def test_real_html_processing(self, mock_get):
        """Test with realistic HTML content"""
        # Load test HTML file
        test_html_path = os.path.join(os.path.dirname(__file__), 'data', 'test_article.html')
        
        # If the test file doesn't exist, create it
        if not os.path.exists(os.path.dirname(test_html_path)):
            os.makedirs(os.path.dirname(test_html_path))
            
        if not os.path.exists(test_html_path):
            with open(test_html_path, 'w', encoding='utf-8') as f:
                f.write("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Test Article Page</title>
                </head>
                <body>
                    <header>
                        <nav>Site Navigation</nav>
                    </header>
                    <main>
                        <article>
                            <h1>Main Article Title</h1>
                            <p>This is the first paragraph of the article which contains important information.</p>
                            <p>This is the second paragraph with more details about the topic.</p>
                            <ul>
                                <li>Important point one</li>
                                <li>Important point two</li>
                            </ul>
                            <p>Final paragraph with conclusion.</p>
                        </article>
                    </main>
                    <footer>
                        Copyright notice and links
                    </footer>
                </body>
                </html>
                """)
        
        # Read the test HTML
        with open(test_html_path, 'rb') as f:
            test_html = f.read()
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_html
        mock_get.return_value = mock_response
        
        # Create processor and fetcher
        processor = ContentProcessor()
        
        # Process the HTML content directly
        processed = processor.process_content(test_html, url="https://example.com/test-article")
        
        # Verify main content extraction
        self.assertIn("Main Article Title", processed["text"])
        self.assertIn("important information", processed["text"])
        self.assertIn("Important point one", processed["text"])
        
        # Navigation and footer should be removed
        self.assertNotIn("Site Navigation", processed["text"])
        self.assertNotIn("Copyright notice", processed["text"])

if __name__ == "__main__":
    unittest.main()