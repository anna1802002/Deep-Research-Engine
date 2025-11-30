import logging
import requests
import numpy as np
import torch
import os
import yaml
import hashlib
from typing import List, Dict, Union, Optional

class ContentEmbedder:
    """Generates vector embeddings for content chunks."""
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.logger = logging.getLogger("deep_research.ranking.embedder")
        self.model_name = model_name
        self.api_key = self._load_api_key()
        
        # Local model will be loaded on demand
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def _load_api_key(self) -> str:
        """Load OpenAI API key from config."""
        config_path = "config/api_keys.yaml"
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as file:
                    config = yaml.safe_load(file)
                    return config.get("OPENAI_API_KEY", "")
            return ""
        except Exception as e:
            self.logger.error(f"Error loading API key: {e}")
            return ""
    
    def embed_content(self, text: str) -> List[float]:
        """
        Generate embedding for content text.
        Tries multiple methods with fallbacks.
        
        Args:
            text: Text to embed
            
        Returns:
            Vector embedding
        """
        # Try different embedding methods with fallbacks
        methods = [
            self._api_embedding,  # OpenAI API
            self._local_embedding,  # Local model
            self._mock_embedding   # Fallback mock
        ]
        
        for method in methods:
            try:
                embedding = method(text)
                if embedding:
                    return embedding
            except Exception as e:
                self.logger.warning(f"Embedding method failed: {e}")
        
        # If all methods fail, use mock embedding
        self.logger.warning("All embedding methods failed, using mock embedding")
        return self._mock_embedding(text)
    
    def _api_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI API."""
        if not self.api_key:
            return None
            
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "input": text,
            "model": "text-embedding-3-small"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        
        if "data" in response_data and len(response_data["data"]) > 0:
            return response_data["data"][0]["embedding"]
        
        self.logger.error(f"API Error: {response_data}")
        return None
    
    def _local_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using local model."""
        if self.model is None:
            try:
                self._load_model()
            except Exception as e:
                self.logger.error(f"Failed to load local model: {e}")
                return None
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"Error generating local embedding: {e}")
            return None
    
    def _load_model(self):
        """Load local embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.logger.info(f"Loaded local model: {self.model_name} on {self.device}")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise
    
    def _mock_embedding(self, text: str) -> List[float]:
        """Generate deterministic mock embedding."""
        # Create hash of text
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to numpy array
        np_array = np.frombuffer(hash_bytes, dtype=np.uint8)
        
        # Normalize to values between -1 and 1
        embedding = (np_array.astype(np.float32) / 128.0) - 1.0
        
        # Ensure consistent length (1536 dimensions like OpenAI embeddings)
        while len(embedding) < 1536:
            embedding = np.concatenate([embedding, embedding])
        
        return embedding[:1536].tolist()
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between embeddings."""
        if not embedding1 or not embedding2:
            return 0.0
            
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Compute cosine similarity
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return np.dot(vec1, vec2) / (norm1 * norm2)