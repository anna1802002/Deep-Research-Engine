import json
import os
import sys

# Ensure the script recognizes the src module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.storage.storage_manager import StorageManager

class Deduplicator:
    """Handles deduplication of metadata and citations."""
    
    def __init__(self):
        self.storage = StorageManager()
    
    def remove_duplicates(self, data, key_fields):
        """Removes duplicate entries based on key fields."""
        seen = set()
        unique_data = []
        
        for entry in data:
            # Ensure entry is a dictionary
            if not isinstance(entry, dict):
                print(f"⚠️ Skipping invalid metadata entry: {entry}")
                continue

            identifier = tuple(entry.get(field, "").lower() for field in key_fields)
            if identifier not in seen:
                seen.add(identifier)
                unique_data.append(entry)

        return unique_data

    def deduplicate_metadata(self):
        """Load, deduplicate, and save validated metadata."""
        metadata = self.storage.load_validated_metadata()
        if not metadata:
            print("⚠️ No metadata found for deduplication.")
            return
        
        deduplicated = self.remove_duplicates(metadata, ["title", "doi", "url"])
        self.storage.save_validated_metadata(deduplicated)
        print(f"✅ Deduplicated {len(metadata) - len(deduplicated)} duplicate metadata entries.")

    def deduplicate_citations(self):
        """Load, deduplicate, and save extracted citations."""
        citations = self.storage.load_citations()
        if not citations:
            print("⚠️ No citations found for deduplication.")
            return
        
        deduplicated = self.remove_duplicates(citations, ["title", "doi"])
        self.storage.save_citations(deduplicated)
        print(f"✅ Deduplicated {len(citations) - len(deduplicated)} duplicate citations.")

# ✅ Test the Deduplicator
if __name__ == "__main__":
    deduplicator = Deduplicator()
    deduplicator.deduplicate_metadata()
    deduplicator.deduplicate_citations()
