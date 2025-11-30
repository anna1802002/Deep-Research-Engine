import json
import os

class StorageManager:
    """Handles loading and saving metadata, citations, and processed data."""
    
    def __init__(self, storage_dir="data_storage"):
        """Initialize the storage directory."""
        self.storage_dir = storage_dir
        self.metadata_file = os.path.join(self.storage_dir, "validated_metadata.json")
        self.citations_file = os.path.join(self.storage_dir, "citations.json")

        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)

    def load_validated_metadata(self):
        """Load validated metadata from JSON storage."""
        if not os.path.exists(self.metadata_file):
            print("🔴 Metadata file not found! Returning empty list.")
            return []
        
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("⚠️ Error decoding metadata JSON. Returning empty list.")
            return []

    def save_validated_metadata(self, metadata):
        """Save validated metadata to JSON storage."""
        with open(self.metadata_file, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)
        print("✅ Validated metadata saved successfully!")

    def load_citations(self):
        """Load extracted citations from JSON storage."""
        if not os.path.exists(self.citations_file):
            print("🔴 Citations file not found! Returning empty list.")
            return []
        
        try:
            with open(self.citations_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("⚠️ Error decoding citations JSON. Returning empty list.")
            return []

    def save_citations(self, citations):
        """Save extracted citations to JSON storage."""
        with open(self.citations_file, "w", encoding="utf-8") as file:
            json.dump(citations, file, indent=4)
        print("✅ Citations saved successfully!")

# ✅ Test StorageManager
if __name__ == "__main__":
    storage = StorageManager()

    # Test saving and loading metadata
    sample_metadata = [{"title": "AI in Healthcare", "doi": "10.1234/ai-health", "url": "https://example.com"}]
    storage.save_validated_metadata(sample_metadata)
    print("Loaded Metadata:", storage.load_validated_metadata())

    # Test saving and loading citations
    sample_citations = [{"title": "Machine Learning Advances", "doi": "10.5678/ml-adv"}]
    storage.save_citations(sample_citations)
    print("Loaded Citations:", storage.load_citations())
