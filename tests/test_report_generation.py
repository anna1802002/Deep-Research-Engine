# tests/test_report_generation.py
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.report_generation.generator import ReportGenerator

def test_report_generation():
    """Test report generation with sample data"""
    # Create sample query and chunks
    query = "artificial intelligence ethics"
    sample_chunks = [
        {
            "text": "AI systems should be designed to align with human values and operate transparently.",
            "metadata": {
                "title": "Ethics in AI Development",
                "source": "Research Paper",
                "url": "https://example.com/paper1"
            }
        },
        {
            "text": "Bias in training data can lead to unfair outcomes in AI decision-making systems.",
            "metadata": {
                "title": "Bias in Machine Learning",
                "source": "Academic Journal",
                "url": "https://example.com/paper2"
            }
        }
    ]
    
    # Create temporary output directory
    output_dir = os.path.join(project_root, "test_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create generator
    generator = ReportGenerator(output_dir=output_dir)
    
    try:
        # Generate report
        result = generator.generate_and_store_report(query, sample_chunks)
        
        print(f"Generated report with ID: {result['report_id']}")
        print(f"Report saved to: {result['file_path']}")
        
        # Print report snippet
        print("\nReport preview:")
        print("-------------------")
        print(result['content'][:300] + "...")
        print("-------------------")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_report_generation()