# tests/test_web_fetcher.py

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_retrieval.web_fetcher import WebFetcher

class TestWebFetcher(unittest.TestCase):
    
    def setUp(self):
        self.fetcher = WebFetcher(timeout=5)
        
    @patch('requests.Session.get')
    def test_fetch_url_success(self, mock_get):
        """Test successful URL fetching"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body><h1>Test Content</h1></body></html>"
        mock_get.return_value = mock_response
        
        # Test fetch
        result = self.fetcher.fetch_url("https://example.com/test")
        
        # Verify request was made correctly
        mock_get.assert_called_once()
        self.assertIsNotNone(result)
        self.assertIn("Test Content", result["text"])
        
    @patch('requests.Session.get')
    def test_fetch_url_error(self, mock_get):
        """Test error handling during fetch"""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Test fetch
        result = self.fetcher.fetch_url("https://example.com/notfound")
        
        # Should handle error gracefully
        self.assertIsNone(result)
        
    @patch('requests.Session.get')
    def test_connection_error(self, mock_get):
        """Test connection error handling"""
        # Mock connection error
        mock_get.side_effect = Exception("Connection error")
        
        # Test fetch
        result = self.fetcher.fetch_url("https://example.com/error")
        
        # Should handle error gracefully
        self.assertIsNone(result)
        
    @patch('src.data_retrieval.web_fetcher.WebFetcher.fetch_url')
    def test_fetch_multiple(self, mock_fetch_url):
        """Test fetching multiple URLs"""
        # Mock individual fetch results
        def mock_fetch_side_effect(url):
            if "success" in url:
                return {"text": f"Content for {url}", "metadata": {"url": url}}
            return None
            
        mock_fetch_url.side_effect = mock_fetch_side_effect
        
        # Test URLs
        urls = [
            "https://example.com/success1",
            "https://example.com/fail",
            "https://example.com/success2"
        ]
        
        results = self.fetcher.fetch_multiple(urls, max_concurrent=2)
        
        # Should have 2 successful results
        self.assertEqual(2, len(results))
        self.assertEqual(3, mock_fetch_url.call_count)
        
    def test_invalid_url(self):
        """Test handling of invalid URLs"""
        result = self.fetcher.fetch_url("not-a-valid-url")
        self.assertIsNone(result)
        
        result = self.fetcher.fetch_url(None)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()