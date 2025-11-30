# tests/test_content_processor.py

import sys
import os
import unittest
import tempfile
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_retrieval.content_processor import ContentProcessor

class TestContentProcessor(unittest.TestCase):
    
    def setUp(self):
        # Create temporary cache directory
        self.temp_cache_dir = tempfile.mkdtemp()
        self.processor = ContentProcessor(cache_dir=self.temp_cache_dir)
        
        # Sample content
        self.html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <main>
                <h1>Test Article</h1>
                <p>This is test content for processing.</p>
            </main>
        </body>
        </html>
        """
        
        self.text_content = "This is plain text content with   extra   spaces   that should be normalized."
        
    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.temp_cache_dir)
        
    def test_process_html_content(self):
        """Test HTML content processing"""
        result = self.processor.process_content(self.html_content, url="https://example.com/test.html")
        
        # Check text extraction
        self.assertIn("Test Article", result["text"])
        self.assertIn("test content for processing", result["text"])
        
        # Check metadata
        self.assertEqual("text", result["metadata"]["content_type"])
        self.assertEqual("html", result["metadata"]["subtype"])
        self.assertEqual("https://example.com/test.html", result["metadata"]["url"])
        self.assertEqual("passed", result["metadata"]["validation_status"])
        
    def test_process_text_content(self):
        """Test plain text processing"""
        result = self.processor.process_content(self.text_content, url="https://example.com/test.txt")
        
        # Check text normalization
        self.assertEqual("This is plain text content with extra spaces that should be normalized.", result["text"])
        
        # Check metadata
        self.assertEqual("text", result["metadata"]["content_type"])
        
    def test_content_validation(self):
        """Test content validation logic"""
        # Too short content
        short_text = "Too short"
        self.assertFalse(self.processor._validate_content(short_text))
        
        # Good content
        good_text = "This is a reasonably long piece of text that should pass validation. It contains multiple sentences and a good amount of words."
        self.assertTrue(self.processor._validate_content(good_text))
        
        # Too many special characters
        bad_text = "^^^###!! This text has too many special @@@@@@@ characters &&&&&& to be valid #$#$#$#$"
        self.assertFalse(self.processor._validate_content(bad_text))
        
    def test_text_normalization(self):
        """Test text normalization"""
        text = "Text with  multiple   spaces\t\nand line\rbreaks."
        normalized = self.processor._normalize_text(text)
        self.assertEqual("Text with multiple spaces and line breaks.", normalized)
        
        # Test smart quotes normalization
        smart_quotes = "This has \"smart quotes\" and 'smart apostrophes'"
        normalized = self.processor._normalize_text(smart_quotes)
        self.assertEqual('This has "smart quotes" and \'smart apostrophes\'', normalized)
        
    def test_caching(self):
        """Test content caching functionality"""
        url = "https://example.com/cache-test.html"
        
        # Process content for the first time
        result1 = self.processor.process_content(self.html_content, url=url)
        content_hash = result1["metadata"]["hash"]
        
        # Check if cache file was created
        cache_file = os.path.join(self.temp_cache_dir, f"{content_hash}.json")
        self.assertTrue(os.path.exists(cache_file))
        
        # Process same content again, should use cache
        result2 = self.processor.process_content(self.html_content, url=url)
        
        # Results should be identical
        self.assertEqual(result1["text"], result2["text"])
        self.assertEqual(result1["metadata"]["hash"], result2["metadata"]["hash"])

if __name__ == "__main__":
    unittest.main()