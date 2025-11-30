import logging
from typing import Dict, Any, List

from src.query_processing.expander import QueryExpander
from src.query_processing.parser import QueryParser
from src.query_processing.vectorizer import QueryVectorizer

class QueryProcessingOrchestrator:
    """
    Orchestrates the entire query processing workflow.
    Combines expansion, parsing, and vectorization into a unified pipeline.
    """
    
    def __init__(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("deep_research.query_orchestrator")
        
        # Initialize processing components
        self.expander = QueryExpander()
        self.parser = QueryParser()
        self.vectorizer = QueryVectorizer()
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query through the entire pipeline.
        
        Args:
            query: Raw query string
            
        Returns:
            Processed query dictionary with all metadata
        """
        try:
            # Step 1: Expand the query 
            expanded_query = self.expander.expand_query(query)
            self.logger.info(f"Expanded Query: {expanded_query}")
            
            # Step 2: Clean the expanded query (instead of parsing)
            cleaned_query = self.parser.clean_query(expanded_query)
            self.logger.info(f"Cleaned Query: {cleaned_query}")
            
            # Step 3: Generate vector embedding using the cleaned query
            embedding = self.vectorizer.vectorize_query(cleaned_query)
            
            # Combine all processing results
            processed_query = {
                "original_query": query,
                "expanded_query": expanded_query,
                "cleaned_query": cleaned_query,
                "query_embedding": embedding,
                "metadata": {
                    "embedding_size": len(embedding),
                    "expanded_terms_count": len(expanded_query.split(', ')) if expanded_query else 0
                }
            }
            
            return processed_query
        
        except Exception as e:
            self.logger.error(f"Query processing error: {e}")
            return {
                "error": str(e),
                "original_query": query
            }
    
    def batch_process_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple queries in sequence.
        
        Args:
            queries: List of query strings
            
        Returns:
            List of processed query dictionaries
        """
        return [self.process_query(query) for query in queries]
    
    def validate_processed_query(self, processed_query: Dict[str, Any]) -> bool:
        """
        Validate the processed query result.
        
        Args:
            processed_query: Processed query dictionary
            
        Returns:
            Boolean indicating query processing success
        """
        # Check for basic validity
        if 'error' in processed_query:
            return False
        
        checks = [
            processed_query.get('expanded_query'),
            processed_query.get('cleaned_query'),
            processed_query.get('query_embedding')
        ]
        
        return all(checks)

def main():
    """
    Example usage of the QueryProcessingOrchestrator.
    """
    orchestrator = QueryProcessingOrchestrator()
    
    # Example queries
    sample_queries = [
        "machine learning techniques",
        "quantum computing research",
        "climate change impact"
    ]
    
    # Process queries
    for result in orchestrator.batch_process_queries(sample_queries):
        print("\nProcessed Query Result:")
        print(f"Original Query: {result.get('original_query')}")
        print(f"Expanded Query: {result.get('expanded_query')}")
        print(f"Cleaned Query: {result.get('cleaned_query')}")
        print(f"Embedding Size: {result.get('metadata', {}).get('embedding_size')}")
        print(f"Validation: {orchestrator.validate_processed_query(result)}")

if __name__ == '__main__':
    main()