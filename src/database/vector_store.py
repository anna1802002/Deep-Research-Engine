import chromadb
import hashlib
from datetime import datetime
import typing

class ChromaDBManager:
    def __init__(self, path: str = "./chroma_storage"):
        """
        Initialize ChromaDB client with a specified storage path.
        
        :param path: Directory path for storing ChromaDB collections
        """
        self.client = chromadb.PersistentClient(path=path)
    
    def get_or_create_collection(self, collection_name: str):
        """
        Get or create a ChromaDB collection.
        
        :param collection_name: Name of the collection
        :return: ChromaDB collection
        """
        return self.client.get_or_create_collection(name=collection_name)
    
    def store_embedding(self, 
                        collection_name: str, 
                        id: str, 
                        text: str, 
                        embedding: typing.List[float], 
                        metadata: dict = None):
        """
        Store a text embedding in ChromaDB.
        
        :param collection_name: Name of the collection
        :param id: Unique identifier for the embedding
        :param text: Original text content
        :param embedding: Vector representation of the text
        :param metadata: Additional metadata for the embedding
        """
        collection = self.get_or_create_collection(collection_name)
        
        # Default metadata if none provided
        if metadata is None:
            metadata = {}
        
        # Add default timestamp if not present
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()
        
        collection.add(
            ids=[id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )