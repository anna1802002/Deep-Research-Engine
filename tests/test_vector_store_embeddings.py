import os
import sys
import pytest
import numpy as np
import chromadb

# Dynamically adjust the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

# Add logging for debugging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# These are placeholder implementations - you'll need to replace with your actual implementations
class ChromaDBManager:
    def __init__(self, path='./chroma_storage'):
        """
        Initialize ChromaDB Manager
        
        :param path: Path to store ChromaDB collections
        """
        self.client = chromadb.PersistentClient(path=path)
    
    def get_or_create_collection(self, collection_name):
        """
        Get or create a ChromaDB collection
        
        :param collection_name: Name of the collection
        :return: ChromaDB collection
        """
        return self.client.get_or_create_collection(name=collection_name)
    
    def store_embedding(self, collection_name, id, text, embedding, metadata=None):
        """
        Store an embedding in the specified collection
        
        :param collection_name: Name of the collection
        :param id: Unique identifier for the embedding
        :param text: Text content
        :param embedding: Embedding vector
        :param metadata: Optional metadata
        """
        # Validate embedding
        if not embedding or not isinstance(embedding, list):
            raise ValueError("Invalid embedding: must be a non-empty list")
        
        # Ensure embedding is a list of floats
        if not all(isinstance(x, (int, float)) for x in embedding):
            raise ValueError("Embedding must contain numeric values")
        
        # Get or create collection
        collection = self.get_or_create_collection(collection_name)
        
        # Store embedding
        collection.add(
            ids=[id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata] if metadata else [{}]
        )
    
    def search_embeddings(self, collection_name, query_embedding, n_results=2):
        """
        Perform similarity search in a collection
        
        :param collection_name: Name of the collection
        :param query_embedding: Query embedding vector
        :param n_results: Number of results to return
        :return: Search results
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

class ContentEmbedder:
    def __init__(self, embedding_dim=384):
        """
        Initialize content embedder
        
        :param embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
    
    def embed_content(self, text):
        """
        Generate a simple embedding for given text
        
        :param text: Input text
        :return: Embedding vector
        """
        # Simple deterministic embedding generation
        # In a real scenario, you'd use a proper embedding model
        base_embedding = [
            sum(ord(c) for c in text) / len(text),  # Average character value
            len(text),  # Text length
            text.count(' '),  # Word count approximation
        ]
        
        # Pad or truncate to specified embedding dimension
        while len(base_embedding) < self.embedding_dim:
            base_embedding.append(0.0)
        
        return base_embedding[:self.embedding_dim]

class TestVectorStoreEmbeddings:
    @pytest.fixture(scope="function")
    def temp_storage_path(self, tmp_path):
        """Create a temporary storage path for ChromaDB using pytest's tmp_path."""
        test_path = tmp_path / "chroma_storage"
        test_path.mkdir(parents=True, exist_ok=True)
        return str(test_path)

    @pytest.fixture(scope="function")
    def chroma_manager(self, temp_storage_path):
        """Create a ChromaDBManager instance for testing."""
        try:
            return ChromaDBManager(path=temp_storage_path)
        except Exception as e:
            logger.error(f"Failed to create ChromaDBManager: {e}")
            pytest.fail(f"ChromaDBManager initialization failed: {e}")

    @pytest.fixture(scope="function")
    def content_embedder(self):
        """Create a ContentEmbedder instance for testing."""
        try:
            return ContentEmbedder()
        except Exception as e:
            logger.error(f"Failed to create ContentEmbedder: {e}")
            pytest.fail(f"ContentEmbedder initialization failed: {e}")

    def test_embedding_storage_and_retrieval(self, chroma_manager, content_embedder):
        """
        Test the full workflow of embedding generation, storage, and retrieval.
        """
        # Test documents
        test_documents = [
            "Machine learning transforms industries",
            "Artificial intelligence drives innovation",
            "Data science enables complex problem solving"
        ]

        collection_name = "test_embedding_collection"

        # Store embeddings
        for idx, doc in enumerate(test_documents):
            # Generate embedding
            embedding = content_embedder.embed_content(doc)
            
            # Validate embedding
            assert len(embedding) > 0, f"Embedding generation failed for document {idx}"
            assert isinstance(embedding, list), "Embedding must be a list"
            
            # Store in ChromaDB
            try:
                chroma_manager.store_embedding(
                    collection_name=collection_name,
                    id=f"doc_{idx}",
                    text=doc,
                    embedding=embedding,
                    metadata={"source": "test_suite", "index": idx}
                )
            except Exception as e:
                logger.error(f"Failed to store embedding for document {idx}: {e}")
                pytest.fail(f"Embedding storage failed: {e}")

        # Retrieve collection
        collection = chroma_manager.get_or_create_collection(collection_name)
        
        # Verify storage
        assert collection.count() == len(test_documents), "Not all documents were stored"

    def test_similarity_search(self, chroma_manager, content_embedder):
        """
        Test embedding similarity search functionality.
        """
        collection_name = "similarity_search_test"
        
        # Prepare test documents
        test_documents = [
            "Machine learning algorithms are powerful",
            "AI and machine learning techniques",
            "Deep learning revolutionizes technology",
            "Python is great for data science"
        ]

        # Store embeddings
        for idx, doc in enumerate(test_documents):
            embedding = content_embedder.embed_content(doc)
            chroma_manager.store_embedding(
                collection_name=collection_name,
                id=f"doc_{idx}",
                text=doc,
                embedding=embedding
            )

        # Perform similarity search
        query_text = "advanced machine learning techniques"
        query_embedding = content_embedder.embed_content(query_text)
        
        # Search embeddings
        search_results = chroma_manager.search_embeddings(
            collection_name=collection_name,
            query_embedding=query_embedding,
            n_results=2
        )

        # Verify search results
        assert 'ids' in search_results, "Search results missing 'ids' key"
        assert len(search_results['ids'][0]) > 0, "No search results returned"
        assert len(search_results['ids'][0]) <= 2, "More results returned than expected"

    def test_error_handling(self, chroma_manager, content_embedder):
        """
        Test error scenarios in embedding storage.
        """
        collection_name = "error_test_collection"

        # Test invalid embedding scenarios
        with pytest.raises((ValueError, IndexError), match="Invalid embedding|Expected Embeddings"):
            # Generate a valid embedding first
            valid_embedding = content_embedder.embed_content("Some valid text")
            
            # Now try to store an invalid embedding
            chroma_manager.store_embedding(
                collection_name=collection_name,
                id="invalid_doc",
                text="Test document",
                embedding=[],  # Empty embedding
                metadata=None
            )

# Optionally include this if you want to run tests directly
if __name__ == "__main__":
    pytest.main([__file__])