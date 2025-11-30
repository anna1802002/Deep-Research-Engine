# src/examples/test_chunking_chromadb.py

import os
import sys
from src.data_retrieval.content_processor import ContentProcessor
from src.storage.chromadb_integration import ChromaDBIntegration

def test_chunking_with_chromadb():
    """Test chunking and ChromaDB integration."""
    # Create test document
    test_document = """# Research on Quantum Computing
    
Quantum computing is an emerging field that combines quantum physics and computer science.

## Key Concepts

Quantum computers use quantum bits or "qubits" which can exist in multiple states simultaneously.

### Quantum Superposition

Superposition allows qubits to be in multiple states at the same time, unlike classical bits.

### Quantum Entanglement

Entanglement creates a connection between qubits where the state of one qubit depends on another.

## Applications

Quantum computers excel at specific tasks:

1. Cryptography
2. Optimization problems
3. Material science
4. Drug discovery

## Challenges

Despite progress, quantum computers face significant challenges:

- Decoherence
- Error correction
- Scaling up qubits
- Programming paradigms
"""

    # Initialize processors
    content_processor = ContentProcessor(chunk_size=200, chunk_overlap=50)
    chromadb_integration = ChromaDBIntegration(collection_name="test_chunks")
    
    print("1. Testing content processing with chunking...")
    processed = content_processor.process_content(
        test_document,
        url="https://example.com/quantum-research",
        source_type="test"
    )
    
    print(f"   Document processed into {len(processed.get('chunks', []))} chunks")
    
    print("\n2. Storing chunks in ChromaDB...")
    stored_count = chromadb_integration.store_processed_content(processed)
    print(f"   {stored_count} chunks stored in ChromaDB")
    
    print("\n3. Testing search...")
    results = chromadb_integration.search("quantum superposition", n_results=2)
    
    print(f"   Found {len(results)} results for 'quantum superposition'")
    for i, result in enumerate(results):
        print(f"\n   Result {i+1}:")
        print(f"   Score: {result.get('score')}")
        if 'metadata' in result:
            print(f"   Chunk: {result['metadata'].get('chunk_index', 0)+1} of {result['metadata'].get('total_chunks', 1)}")
        text_preview = result.get('text', '')[:100] + "..." if len(result.get('text', '')) > 100 else result.get('text', '')
        print(f"   Preview: {text_preview}")

if __name__ == "__main__":
    test_chunking_with_chromadb()