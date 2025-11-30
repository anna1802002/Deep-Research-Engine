import unittest
import logging
from typing import Dict, Any
import sys
import os
import time

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.query_processing.expander import QueryExpander
from src.query_processing.parser import QueryParser
from src.query_processing.vectorizer import QueryVectorizer

class TestQueryProcessing(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test method."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        
        # Initialize components
        self.expander = QueryExpander()
        self.parser = QueryParser()
        self.vectorizer = QueryVectorizer()
    
    def test_query_expander(self):
        """Test query expansion functionality."""
        test_cases = [
            "ai",
            "machine learning",
            "quantum computing",
            "climate change",
            None,
            "",
            42,
            ["not a string"]
        ]
        
        for query in test_cases:
            with self.subTest(query=query):
                expanded_query = self.expander.expand_query(query)
                
                # Check that expansion returns a non-empty string
                self.assertIsNotNone(expanded_query)
                self.assertTrue(isinstance(expanded_query, str))
                
                # For non-empty original queries, check expansion
                if query and isinstance(query, str) and query.strip():
                    self.assertTrue(len(expanded_query) > len(str(query)))
    
    def test_query_parser(self):
        """Test query parsing functionality."""
        test_queries = [
            "Tell me about artificial intelligence",
            "How to understand machine learning",
            "Explain quantum computing research",
            None,
            "",
            42,
            ["not a string"]
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                parsed_query = self.parser.parse_query(query)
                
                # Validate parsed query structure
                self._validate_parsed_query(parsed_query)
    
    def _validate_parsed_query(self, parsed_query: Dict[str, Any]):
        """Helper method to validate parsed query structure."""
        expected_keys = ['original', 'cleaned', 'key_terms']
        
        # Check all expected keys are present
        for key in expected_keys:
            self.assertIn(key, parsed_query)
        
        # Validate key_terms is a list
        self.assertIsInstance(parsed_query['key_terms'], list)
    
    def test_query_vectorizer(self):
        """Test query vectorization functionality."""
        test_queries = [
            "artificial intelligence",
            "machine learning algorithms",
            "quantum computing research",
            None,
            "",
            42,
            ["not a string"]
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                embedding = self.vectorizer.vectorize_query(query)
                
                # Check embedding properties
                self.assertIsNotNone(embedding)
                self.assertEqual(len(embedding), 1536)  # Consistent embedding size
                self.assertTrue(all(-1 <= x <= 1 for x in embedding))  # Values between -1 and 1
    
    def test_query_processing_integration(self):
        """Test integrated query processing workflow."""
        test_queries = [
            "advanced machine learning techniques",
            "latest developments in artificial intelligence",
            "sustainable energy technologies",
            None,
            "",
            42
        ]
        
        for sample_query in test_queries:
            with self.subTest(query=sample_query):
                # Expanded query
                expanded_query = self.expander.expand_query(sample_query)
                self.assertIsNotNone(expanded_query)
                
                # Parsed query
                parsed_query = self.parser.parse_query(expanded_query)
                self._validate_parsed_query(parsed_query)
                
                # Vectorized query
                embedding = self.vectorizer.vectorize_query(expanded_query)
                self.assertEqual(len(embedding), 1536)
    
    def test_query_performance(self):
        """Basic performance sanity check for query processing."""
        test_queries = [
            "machine learning",
            "artificial intelligence research",
            "quantum computing advancements"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                # Measure expansion time
                start_time = time.time()
                expanded_query = self.expander.expand_query(query)
                expansion_time = time.time() - start_time
                
                # Measure parsing time
                start_time = time.time()
                parsed_query = self.parser.parse_query(expanded_query)
                parsing_time = time.time() - start_time
                
                # Measure vectorization time
                start_time = time.time()
                embedding = self.vectorizer.vectorize_query(expanded_query)
                vectorization_time = time.time() - start_time
                
                # More lenient performance thresholds
                self.assertLess(expansion_time, 1.0)     # Expansion should take less than 1s
                self.assertLess(parsing_time, 1.0)       # Parsing should take less than 1s
                self.assertLess(vectorization_time, 2.0) # Vectorization should take less than 2s

if __name__ == '__main__':
    unittest.main()