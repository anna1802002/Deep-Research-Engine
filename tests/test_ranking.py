# tests/test_ranking.py
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.ranking.ranking_system import RankingSystem

def test_ranking():
    """Test the ranking system with sample data"""
    # Create sample query and chunks
    query = "quantum computing applications"
    sample_chunks = [
        {
            "text": "Quantum computing is revolutionizing cryptography and security.",
            "metadata": {"source": "Sample Source 1"}
        },
        {
            "text": "Machine learning algorithms are getting more sophisticated.",
            "metadata": {"source": "Sample Source 2"}
        },
        {
            "text": "Quantum algorithms can solve certain problems exponentially faster.",
            "metadata": {"source": "Sample Source 3"}
        }
    ]
    
    # Create ranking system
    ranking_system = RankingSystem()
    
    try:
        # Process query
        processed_query = ranking_system.process_query(query)
        print(f"Processed query: {processed_query['text']}")
        print(f"Generated embedding with {len(processed_query['metadata'].get('embedding', []))} dimensions")
        
        # Rank content
        result = ranking_system.process_and_rank(query, sample_chunks)
        
        print(f"Ranked {len(result['ranked_chunks'])} chunks")
        
        # Print ranked chunks
        for i, chunk in enumerate(result['ranked_chunks']):
            score = chunk.get('metadata', {}).get('final_score', 0)
            print(f"  {i+1}. {chunk['text']} (score: {score:.2f})")
            
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_ranking()