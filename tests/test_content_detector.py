# tests/test_content_detector.py

import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_retrieval.content_detector import ContentDetector

class TestContentDetector(unittest.TestCase):
    
    def setUp(self):
        self.detector = ContentDetector()
        
        # Sample content for testing
        self.html_content = b"<!DOCTYPE html><html><body><p>Test</p></body></html>"
        self.text_content = b"This is plain text content for testing."
        self.pdf_header = b"%PDF-1.4\n%FAKE PDF CONTENT"
        
    def test_detect_html(self):
        """Test HTML content detection"""
        content_type, subtype = self.detector.detect_type(self.html_content)
        self.assertEqual("text", content_type)
        self.assertEqual("html", subtype)
        
    def test_detect_text(self):
        """Test plain text content detection"""
        content_type, subtype = self.detector.detect_type(self.text_content)
        self.assertEqual("text", content_type)
        # Subtype might be 'plain' or determined by magic library
        
    def test_detect_pdf(self):
        """Test PDF content detection"""
        content_type, subtype = self.detector.detect_type(self.pdf_header)
        # Either application/pdf or application/octet-stream depending on magic library
        self.assertTrue(content_type in ["application", "document"])
        
    def test_url_extension_detection(self):
        """Test URL extension detection logic"""
        ext = self.detector._get_extension_from_url("https://example.com/document.pdf")
        self.assertEqual("pdf", ext)
        
        ext = self.detector._get_extension_from_url("https://example.com/path/file.txt?query=param")
        self.assertEqual("txt", ext)
        
        # No extension
        ext = self.detector._get_extension_from_url("https://example.com/noextension")
        self.assertIsNone(ext)
        
    def test_is_processable(self):
        """Test processable content type determination"""
        self.assertTrue(self.detector.is_processable("text", "html"))
        self.assertTrue(self.detector.is_processable("text", "plain"))
        self.assertTrue(self.detector.is_processable("application", "pdf"))
        self.assertTrue(self.detector.is_processable("document", "pdf"))
        
        self.assertFalse(self.detector.is_processable("image", "jpeg"))
        self.assertFalse(self.detector.is_processable("video", "mp4"))
        
    def test_empty_content(self):
        """Test behavior with empty content"""
        content_type, subtype = self.detector.detect_type(b"")
        self.assertEqual("unknown", content_type)
        self.assertEqual("empty", subtype)

if __name__ == "__main__":
    unittest.main()