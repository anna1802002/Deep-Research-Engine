# tests/test_html_cleaner.py

import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_retrieval.html_cleaner import HTMLCleaner

class TestHTMLCleaner(unittest.TestCase):
    
    def setUp(self):
        self.cleaner = HTMLCleaner()
        
        # Sample HTML content for testing
        self.sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <style>
                body { font-family: Arial; }
            </style>
            <script>
                console.log("This should be removed");
            </script>
        </head>
        <body>
            <header>
                <nav>Navigation links</nav>
            </header>
            <main>
                <h1>Main Article</h1>
                <p>This is the main content that should be extracted.</p>
                <p>It contains <b>important information</b> for testing.</p>
            </main>
            <footer>
                Copyright 2025
            </footer>
        </body>
        </html>
        """
        
    def test_clean_html(self):
        """Test basic HTML cleaning functionality"""
        cleaned = self.cleaner.clean_html(self.sample_html)
        
        # Check that text is extracted
        self.assertIn("Main Article", cleaned)
        self.assertIn("important information", cleaned)
        
        # Check that unwanted elements are removed
        self.assertNotIn("Navigation links", cleaned)
        self.assertNotIn("console.log", cleaned)
        self.assertNotIn("<script>", cleaned)
        self.assertNotIn("<style>", cleaned)
        
    def test_extract_main_content(self):
        """Test main content extraction functionality"""
        main_content = self.cleaner.extract_main_content(self.sample_html)
        
        # Main content should be extracted
        self.assertIn("Main Article", main_content)
        self.assertIn("This is the main content", main_content)
        
        # Header and footer should be removed
        self.assertNotIn("Navigation links", main_content)
        self.assertNotIn("Copyright 2025", main_content)
        
    def test_empty_input(self):
        """Test behavior with empty input"""
        self.assertEqual("", self.cleaner.clean_html(""))
        self.assertEqual("", self.cleaner.extract_main_content(""))
        
    def test_malformed_html(self):
        """Test behavior with malformed HTML"""
        malformed = "<p>Unclosed paragraph<div>Nested content</p>"
        
        # Should not raise an exception
        result = self.cleaner.clean_html(malformed)
        
        # Should extract what it can
        self.assertIn("Unclosed paragraph", result)
        self.assertIn("Nested content", result)

if __name__ == "__main__":
    unittest.main()