import os
import sys

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Just test importing the class first
from src.chunking_engine.dynamic_chunker import DynamicChunker

def test_basic_chunking():
    # Create chunker instance
    chunker = DynamicChunker()
    print("Successfully created DynamicChunker instance!")
    
    # Optionally test a simple method
    # This depends on what methods are actually in your class
    test_text = "This is a test document."
    chunks = chunker.split_document(test_text, 10)
    print(f"Split into {len(chunks)} chunks")

if __name__ == "__main__":
    test_basic_chunking()