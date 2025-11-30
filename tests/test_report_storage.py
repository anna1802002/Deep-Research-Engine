import sys
import os
import unittest

# Ensure the src directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.report_generation.generator import ReportGenerator
from src.database.analytics_store import analytics_store

class TestReportStorage(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.generator = ReportGenerator()
        
    def test_report_generation(self):
        """Test basic report generation."""
        query = "Test search query"
        ranked_chunks = [
            {"text": "First relevant chunk", "metadata": {"source": "doc1"}},
            {"text": "Second relevant chunk", "metadata": {"source": "doc2"}}
        ]
        
        # Generate report
        report = self.generator.generate_report(query, ranked_chunks)
        
        # Basic assertions
        self.assertIsNotNone(report)
        self.assertIn(query, report)
        self.assertIn("First relevant chunk", report)
        self.assertIn("Second relevant chunk", report)
    
    def test_report_storage(self):
        """Test storing a generated report."""
        query = "Complex research query"
        ranked_chunks = [
            {"text": "Detailed information about X", "metadata": {"relevance": 0.9}},
            {"text": "Additional context for X", "metadata": {"relevance": 0.8}}
        ]
        
        # Generate and store report
        result = self.generator.generate_and_store_report(query, ranked_chunks)
        
        # Check report generation details
        self.assertIn("report_id", result)
        self.assertIn("content", result)
        self.assertEqual(result["format"], "markdown")
        
        # Verify report can be retrieved from the database
        # Note: This would require implementing a retrieval method in analytics_store
        # For now, we'll just check that the report_id is a valid string
        self.assertTrue(isinstance(result["report_id"], str))
        self.assertTrue(len(result["report_id"]) > 0)
    
    def test_multiple_report_generations(self):
        """Test generating multiple reports."""
        queries = [
            "First query about technology",
            "Second query about science",
            "Third query about history"
        ]
        
        generated_reports = []
        
        for query in queries:
            ranked_chunks = [
                {"text": f"Sample chunk for {query}", "metadata": {"query": query}}
            ]
            
            report = self.generator.generate_and_store_report(query, ranked_chunks)
            generated_reports.append(report)
        
        # Verify multiple reports were generated
        self.assertEqual(len(generated_reports), 3)
        for report in generated_reports:
            self.assertIn("report_id", report)
            self.assertIn("content", report)
    
    def test_report_format_options(self):
        """Test different report format options."""
        query = "Multiformat report test"
        ranked_chunks = [
            {"text": "Chunk demonstrating format flexibility", "metadata": {"type": "example"}}
        ]
        
        # Test markdown (default)
        markdown_report = self.generator.generate_and_store_report(query, ranked_chunks, format="markdown")
        self.assertEqual(markdown_report["format"], "markdown")
        
        # Future extension: Add more format tests if implemented
        # For example:
        # html_report = self.generator.generate_and_store_report(query, ranked_chunks, format="html")
        # self.assertEqual(html_report["format"], "html")

if __name__ == '__main__':
    unittest.main()