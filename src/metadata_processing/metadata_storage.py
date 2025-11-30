import uuid
import json

class MetadataStorage:
    """Handles storage and retrieval of metadata using ChromaDB."""
    
    def __init__(self):
        """Initialize metadata storage."""
        from src.database.vector_store import get_or_create_collection
        self.collection = get_or_create_collection("metadata")
    
    def store(self, metadata, id=None):
        """Store metadata in ChromaDB."""
        if not id:
            id = str(uuid.uuid4())
        
        # Prepare embedding (placeholder for metadata-only entries)
        embedding = [0.0] * 4
        
        # Flatten metadata to string for ChromaDB document (optional)
        document = json.dumps(metadata)
        
        # Store in ChromaDB
        self.collection.add(
            ids=[id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata]
        )
        
        return id
    
    def retrieve(self, id):
        """Retrieve metadata by ID."""
        results = self.collection.get(ids=[id])
        if results and results["metadatas"]:
            return results["metadatas"][0]
        return None
    
    def search(self, filters=None, limit=10):
        """Search metadata using filters."""
        if not filters:
            results = self.collection.get(limit=limit)
        else:
            # Convert filters to ChromaDB where clauses
            where = {}
            for key, value in filters.items():
                where[key] = value
            
            results = self.collection.get(where=where, limit=limit)
        
        return results["metadatas"] if results else []