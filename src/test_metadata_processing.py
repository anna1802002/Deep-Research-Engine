#!/usr/bin/env python
# test_metadata_processing.py - Test script for metadata processing components

import os
import sys
import json
import logging
from pathlib import Path

# Add the parent directory to Python path to import modules
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import metadata processing components
from src.metadata_processing.metadata_extractor import MetadataExtractor
from src.metadata_processing.metadata_standardizer import MetadataStandardizer
from src.metadata_processing.metadata_validator import MetadataValidator
from src.metadata_processing.metadata_processor import MetadataProcessor
from src.metadata_processing.citation_extractor import CitationExtractor
from src.metadata_processing.standardization import StandardizationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("metadata_test")

def load_sample_data(file_path):
    """Load sample metadata from JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        # Return fallback sample data
        return [
            {
                "title": "Advances in AI for Healthcare",
                "authors": "John Doe, Jane Smith",
                "publication_date": "2024-02-15",
                "abstract": "This paper discusses the latest AI applications in healthcare.",
                "source": "arXiv",
                "url": "https://arxiv.org/abs/1234.5678"
            }
        ]

def test_metadata_extraction():
    """Test metadata extraction from different sources."""
    logger.info("Testing metadata extraction...")
    
    extractor = MetadataExtractor()
    
    # Test ArXiv extraction
    arxiv_data = {
        "title": "Deep Learning for Natural Language Processing",
        "authors": ["John Smith", "Jane Doe"],
        "published": "2023-05-15",
        "id": "https://arxiv.org/abs/2305.12345",
        "categories": ["cs.CL", "cs.AI"],
        "abstract": "This paper explores deep learning techniques for NLP tasks."
    }
    
    arxiv_metadata = extractor.extract_metadata(arxiv_data, "arxiv")
    logger.info(f"Extracted ArXiv metadata: {json.dumps(arxiv_metadata, indent=2)}")
    
    # Test web extraction
    web_data = {
        "title": "The Future of AI",
        "url": "https://example.com/ai-future",
        "published_date": "2023-10-01",
        "authors": "Tech Writer",
        "content": "A detailed exploration of AI's future impact."
    }
    
    web_metadata = extractor.extract_metadata(web_data, "web")
    logger.info(f"Extracted Web metadata: {json.dumps(web_metadata, indent=2)}")
    
    return arxiv_metadata, web_metadata

def test_metadata_standardization(metadata_list):
    """Test metadata standardization."""
    logger.info("Testing metadata standardization...")
    
    standardizer = MetadataStandardizer()
    standardized = standardizer.standardize_metadata(metadata_list)
    
    logger.info(f"Standardized metadata entries: {json.dumps(standardized, indent=2)}")
    return standardized

def test_metadata_validation(metadata_list):
    """Test metadata validation."""
    logger.info("Testing metadata validation...")
    
    validator = MetadataValidator()
    validated = validator.validate_batch(metadata_list)
    
    # Check validation results
    valid_count = sum(1 for m in validated if m.get("_validation", {}).get("valid", False))
    logger.info(f"Validated {len(validated)} metadata entries, {valid_count} valid")
    
    for i, metadata in enumerate(validated):
        validation_info = metadata.get("_validation", {})
        logger.info(f"Entry {i+1}: Valid={validation_info.get('valid')}, Issues={validation_info.get('issues')}")
    
    return validated

def test_metadata_processing(metadata):
    """Test metadata processing and chunk attachment."""
    logger.info("Testing metadata processing...")
    
    processor = MetadataProcessor()
    
    # Process a single metadata entry
    processed = processor.process_metadata(metadata)
    logger.info(f"Processed metadata: {json.dumps(processed, indent=2)}")
    
    # Create some test chunks
    test_chunks = [
        {"text": "This is chunk 1 discussing AI in healthcare."},
        {"text": "This is chunk 2 on medical applications."},
        {"text": "This is chunk 3 about future developments.", "metadata": {"existing": "value"}}
    ]
    
    # Attach metadata to chunks
    enriched_chunks = processor.attach_metadata_to_chunks(test_chunks, processed)
    
    logger.info(f"Created {len(enriched_chunks)} chunks with attached metadata")
    logger.info(f"Sample chunk metadata: {json.dumps(enriched_chunks[0]['metadata'], indent=2)}")
    
    return enriched_chunks

def test_standardization_service(metadata_list):
    """Test the standardization service."""
    logger.info("Testing standardization service...")
    
    service = StandardizationService()
    
    # Standardize metadata
    standardized = service.standardize_metadata(metadata_list)
    logger.info(f"Standardized {len(standardized)} metadata entries using service")
    
    # Create test document with chunks
    test_document = {
        "text": "This is a test document about AI in healthcare.",
        "metadata": metadata_list[0],
        "chunks": [
            {"text": "This is a test chunk about AI applications."},
            {"text": "This is another test chunk about healthcare."}
        ]
    }
    
    # Process document with standardization service
    processed_doc = service.process_document_with_metadata(test_document)
    
    logger.info(f"Processed document with {len(processed_doc['chunks'])} chunks")
    logger.info(f"Document metadata: {json.dumps(processed_doc['metadata'], indent=2)}")
    
    return processed_doc

def save_results(data, filename):
    """Save test results to file."""
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Results saved to {output_dir / filename}")

def main():
    """Main test function."""
    logger.info("Starting metadata processing tests...")
    
    # Load sample data
    sample_data_path = "metadata_output.json"
    metadata_list = load_sample_data(sample_data_path)
    
    # Test extraction
    arxiv_metadata, web_metadata = test_metadata_extraction()
    
    # Combine extracted metadata with sample data
    all_metadata = metadata_list + [arxiv_metadata, web_metadata]
    
    # Test standardization
    standardized = test_metadata_standardization(all_metadata)
    save_results(standardized, "standardized_metadata.json")
    
    # Test validation
    validated = test_metadata_validation(standardized)
    save_results(validated, "validated_metadata.json")
    
    # Test processing with the first validated metadata
    if validated:
        enriched_chunks = test_metadata_processing(validated[0])
        save_results(enriched_chunks, "enriched_chunks.json")
    
    # Test standardization service
    processed_doc = test_standardization_service(all_metadata)
    save_results(processed_doc, "processed_document.json")
    
    logger.info("Metadata processing tests completed successfully!")

if __name__ == "__main__":
    main()