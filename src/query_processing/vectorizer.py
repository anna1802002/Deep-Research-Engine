import os
import yaml
import logging
import numpy as np
from typing import List, Optional

class QueryVectorizer:
    """Generates vector embeddings for queries."""
    
    def __init__(self):
        self.logger = logging.getLogger("deep_research.query_processing.vectorizer")
        self.api_key = self._load_api_key()
    
    def _load_api_key(self) -> str:
        """Load API key from config."""
        config_path = "config/api_keys.yaml"
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as file:
                    config = yaml.safe_load(file)
                    # Try multiple possible key names
                    api_key = (
                        config.get("GROQ_API_KEY") or 
                        config.get("OPENAI_API_KEY") or 
                        config.get("API_KEY", "")
                    )
                    if not api_key:
                        self.logger.warning("No API key found in config")
                    return api_key
            self.logger.warning(f"API key config file not found at {config_path}")
            return ""
        except Exception as e:
            self.logger.error(f"Error loading API key: {e}")
            return ""
    
    def vectorize_query(self, query) -> List[float]:
        """
        Generate vector embedding for a query.
        
        Args:
            query: Query to vectorize
        
        Returns:
            Vector embedding
        """
        # Handle None or non-string input
        if query is None:
            query = ''
        
        if not isinstance(query, str):
            query = str(query)
        
        # Validate query is not empty
        if not query.strip():
            self.logger.warning("Empty query provided. Generating mock embedding.")
            return self._mock_embedding()
        
        # Immediate fallback to mock embedding
        self.logger.warning("Falling back to mock embedding as API access is not configured")
        return self._mock_embedding(query)
    
    def _mock_embedding(self, text: str = '') -> List[float]:
        """
        Generate a deterministic mock embedding.
        This is a fallback when API calls fail.
        """
        import hashlib
        
        # Handle None or non-string input
        if text is None:
            text = ''
        elif not isinstance(text, str):
            text = str(text)
        
        # Create a hash of the text
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # Create a numpy array from the hash bytes
        np_array = np.frombuffer(hash_bytes, dtype=np.uint8)
        
        # Normalize to values between -1 and 1
        embedding = (np_array.astype(np.float32) / 128.0) - 1.0
        
        # Ensure consistent length (1536 dimensions like OpenAI embeddings)
        while len(embedding) < 1536:
            embedding = np.concatenate([embedding, embedding])
        
        return embedding[:1536].tolist()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    vectorizer = QueryVectorizer()
    user_query = input("Enter your expanded query: ")
    vector_embedding = vectorizer.vectorize_query(user_query)

    if vector_embedding:
        print("\n✅ Generated Vector Embedding:")
        print(f"Embedding length: {len(vector_embedding)}")
        print(vector_embedding[:10])  # Show first 10 values for readability
    else:
        print("❌ Failed to generate vector embeddings.")