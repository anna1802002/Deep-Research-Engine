# src/storage/chromadb_integration.py

import os
import logging
import hashlib
from typing import List, Dict, Any
from src.database.chroma_client import ChromaDBManager
from src.chunking_engine.dynamic_chunker import DynamicChunker

logger = logging.getLogger("deep_research")

class ChromaDBIntegration:
    """
    Integration between the chunking engine and ChromaDB storage.
    """
    
    def __init__(self, collection_name="research_chunks", storage_path="./chroma_storage"):
        """
        Initialize ChromaDB integration.
        
        Args:
            collection_name (str): Name of ChromaDB collection
            storage_path (str): Path to ChromaDB storage
        """
        self.logger = logging.getLogger("deep_research.chromadb_integration")
        self.db_manager = ChromaDBManager(path=storage_path)
        self.collection_name = collection_name
        self.chunker = DynamicChunker()
        
    def store_document(self, document_content: str, metadata: Dict[str, Any], chunk_size=1000, chunk_overlap=100):
        """
        Process a document, chunk it, and store in ChromaDB.
        
        Args:
            document_content (str): Document content to process
            metadata (dict): Document metadata
            chunk_size (int): Size of chunks
            chunk_overlap (int): Overlap between chunks
            
        Returns:
            int: Number of chunks stored
        """
        try:
            # Use dynamic chunker to split the document
            chunks = self.chunker.split_document(document_content, chunk_size, chunk_overlap)
            
            # Store each chunk
            for i, chunk_text in enumerate(chunks):
                # Create chunk metadata
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap
                })
                
                # Generate unique ID for the chunk
                chunk_id = self._generate_chunk_id(chunk_text, chunk_metadata)
                
                # Generate a placeholder embedding (you would replace this with your actual embedding model)
                embedding = self._generate_placeholder_embedding(chunk_text)
                
                # Store in ChromaDB
                self.db_manager.store_embedding(
                    collection_name=self.collection_name,
                    id=chunk_id,
                    text=chunk_text,
                    embedding=embedding,
                    metadata=chunk_metadata
                )
            
            self.logger.info(f"Stored {len(chunks)} chunks in ChromaDB")
            return len(chunks)
            
        except Exception as e:
            self.logger.error(f"Error storing document in ChromaDB: {e}")
            return 0
    
    def store_processed_content(self, processed_content):
        """
        Store processed content with existing chunks in ChromaDB.
        
        Args:
            processed_content (dict): Processed content with chunks
            
        Returns:
            int: Number of chunks stored
        """
        if not processed_content:
            print("No processed content to store")
            return 0
            
        print(f"Processed content keys: {processed_content.keys()}")
        
        if "chunks" not in processed_content:
            print("No 'chunks' key in processed content")
            return 0
        
        chunks = processed_content["chunks"]
        print(f"Number of chunks: {len(chunks)}")
        
        if not chunks:
            print("Chunks list is empty")
            return 0
            
        try:
            count = 0
            
            for i, chunk in enumerate(chunks):
                print(f"Processing chunk {i+1}/{len(chunks)}")
                
                if not chunk:
                    print(f"Chunk {i+1} is None or empty, skipping")
                    continue
                    
                if "text" not in chunk:
                    print(f"Chunk {i+1} has no 'text' key, keys: {chunk.keys() if isinstance(chunk, dict) else 'not a dict'}")
                    continue
                    
                text = chunk["text"]
                metadata = chunk.get("metadata", {})
                
                # Generate unique ID for the chunk
                chunk_id = self._generate_chunk_id(text, metadata)
                
                # Generate a placeholder embedding
                embedding = self._generate_placeholder_embedding(text)
                
                print(f"Storing chunk {i+1} with ID {chunk_id}")
                
                # Store in ChromaDB
                self.db_manager.store_embedding(
                    collection_name=self.collection_name,
                    id=chunk_id,
                    text=text,
                    embedding=embedding,
                    metadata=metadata
                )
                
                count += 1
                
            print(f"Successfully stored {count} chunks in ChromaDB")
            self.logger.info(f"Stored {count} chunks in ChromaDB")
            return count
            
        except Exception as e:
            print(f"Error storing processed content in ChromaDB: {e}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"Error storing processed content in ChromaDB: {e}")
            return 0
    
    def search(self, query: str, n_results=5):
        """
        Search for similar chunks to the query.
        
        Args:
            query (str): Search query
            n_results (int): Number of results to return
            
        Returns:
            list: List of matching chunks
        """
        try:
            # In a real implementation, you would:
            # 1. Generate an embedding for the query using the same model used for documents
            # 2. Search ChromaDB using that embedding
            
            # For now, this is a placeholder that uses ChromaDB's text search
            collection = self.db_manager.get_or_create_collection(self.collection_name)
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format the results
            formatted_results = []
            
            if results and 'documents' in results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {}
                    distance = results['distances'][0][i] if 'distances' in results and results['distances'] else None
                    
                    formatted_results.append({
                        "text": doc,
                        "metadata": metadata,
                        "score": 1.0 - (distance / 2) if distance is not None else None  # Convert distance to similarity score
                    })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching ChromaDB: {e}")
            return []
    
    def _generate_chunk_id(self, text, metadata):
        """Generate a unique ID for a chunk based on text and metadata."""
        content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        source = metadata.get('url', metadata.get('file_name', 'unknown'))
        chunk_index = metadata.get('chunk_index', 0)
        
        # Handle source splitting safely
        try:
            source_part = source.split('/')[-1].split('.')[-2]
        except IndexError:
            # Fallback if URL parsing fails
            source_part = "doc"
            
        return f"{source_part}_{chunk_index}_{content_hash[:10]}"
    
    def _generate_placeholder_embedding(self, text, dim=384):
        """
        Generate a placeholder embedding for text.
        In a real implementation, replace with an actual embedding model.
        
        Args:
            text (str): Text to embed
            dim (int): Embedding dimension
            
        Returns:
            list: Embedding vector
        """
        import numpy as np
        # For a deterministic placeholder based on text content
        hash_val = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
        np.random.seed(hash_val % 10000)
        return np.random.randn(dim).tolist()