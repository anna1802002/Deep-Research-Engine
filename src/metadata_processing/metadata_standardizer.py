# src/metadata_processing/metadata_standardizer.py
import re
from typing import List, Dict, Any, Union
import logging

logger = logging.getLogger("deep_research.metadata_processing.standardizer")

class MetadataStandardizer:
    """Standardizes metadata fields for consistency across different sources."""

    def __init__(self):
        """Define standard field mappings."""
        # Field mappings from various source formats to standard format
        self.field_mapping = {
            # Title variations
            "Title": "title",
            "title": "title",
            "Paper Title": "title",
            "document_title": "title",
            
            # Author variations
            "Authors": "authors",
            "Author": "authors",
            "author": "authors",
            "authors": "authors",
            
            # ID variations
            "DOI": "doi",
            "doi": "doi",
            "PMID": "pmid",
            "pmid": "pmid",
            "arxiv_id": "arxiv_id",
            "ArXiv ID": "arxiv_id",
            
            # URL variations
            "URL": "url",
            "Link": "url",
            "source_url": "url",
            "url": "url",
            
            # Date variations
            "publication_date": "publication_date",
            "Published": "publication_date",
            "published": "publication_date",
            "Date": "publication_date",
            "year": "publication_date",
            "Year": "publication_date",
            
            # Source variations
            "Source": "source",
            "source": "source",
            "Journal": "source",
            "journal": "source",
            
            # Abstract/Content
            "Abstract": "abstract",
            "abstract": "abstract",
            "summary": "abstract",
            "content": "content",
            "text": "content",
            
            # Type variations
            "source_type": "source_type",
            "type": "source_type",
            "content_type": "content_type"
        }

    def standardize_metadata(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        Standardize metadata fields across all sources.
        
        Args:
            metadata_list: List of metadata dictionaries to standardize
            
        Returns:
            List of standardized metadata dictionaries
        """
        if not metadata_list:
            logger.warning("Empty metadata list provided for standardization")
            return []
            
        standardized_list = []
        
        for metadata in metadata_list:
            if not metadata:
                logger.warning("Empty metadata entry skipped during standardization")
                continue
                
            standardized_entry = {}
            
            # First pass - standardize all field names
            for key, value in metadata.items():
                # Skip empty or None values
                if value is None or (isinstance(value, str) and not value.strip()):
                    continue
                    
                # Standardize field names
                standard_key = self.field_mapping.get(key, key)
                standardized_entry[standard_key] = value
            
            # Second pass - clean and format field values
            for key in list(standardized_entry.keys()):
                value = standardized_entry[key]
                
                # Clean specific fields
                if key == "doi":
                    standardized_entry[key] = self.clean_doi(value)
                elif key == "url":
                    standardized_entry[key] = self.clean_url(value)
                elif key == "authors":
                    standardized_entry[key] = self.format_authors(value)
                elif key == "publication_date":
                    standardized_entry[key] = self.format_date(value)
                elif key == "source_type":
                    standardized_entry[key] = self.normalize_source_type(value)
            
            # Ensure required fields exist
            self._ensure_required_fields(standardized_entry)
            
            standardized_list.append(standardized_entry)
            
        logger.info(f"Standardized {len(standardized_list)} metadata entries")
        return standardized_list

    def clean_doi(self, doi: Union[str, Any]) -> str:
        """Normalize DOI format."""
        if not doi:
            return ""
        
        if not isinstance(doi, str):
            doi = str(doi)
            
        doi = doi.strip()
        if doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        elif doi.startswith("http://doi.org/"):
            doi = doi.replace("http://doi.org/", "")
        elif doi.startswith("doi:"):
            doi = doi.replace("doi:", "")
            
        return doi

    def clean_url(self, url: Union[str, Any]) -> str:
        """Normalize URLs by ensuring consistency."""
        if not url:
            return ""
            
        if not isinstance(url, str):
            url = str(url)
            
        url = url.strip()
        
        # Ensure URL has proper protocol
        if url and not (url.startswith("http://") or url.startswith("https://")):
            if url.startswith("www."):
                url = "https://" + url
            else:
                url = "https://" + url
                
        return url

    def format_authors(self, authors: Any) -> List[str]:
        """Ensure authors are stored as a list of strings."""
        if not authors:
            return []
            
        if isinstance(authors, str):
            # Split by common separators
            return [author.strip() for author in re.split(r',|;|and', authors) if author.strip()]
        elif isinstance(authors, list):
            # Ensure all entries are strings
            return [str(author).strip() for author in authors if author]
        else:
            # Try to convert to string
            try:
                return [str(authors).strip()]
            except:
                return []

    def format_date(self, date: Any) -> str:
        """Format dates consistently."""
        if not date:
            return ""
            
        if not isinstance(date, str):
            date = str(date)
            
        # If it's just a year (4 digits only)
        if re.match(r'^\d{4}$', date):
            return f"{date}-01-01"  # Default to January 1st
            
        # Already in YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            return date
            
        # Extract year if it exists
        year_match = re.search(r'(?<!\d)(\d{4})(?!\d)', date)
        if year_match:
            return f"{year_match.group(1)}-01-01"  # Default to January 1st
            
        return date

    def normalize_source_type(self, source_type: Any) -> str:
        """Normalize source type to standard values."""
        if not source_type:
            return "unknown"
            
        if not isinstance(source_type, str):
            source_type = str(source_type)
            
        source_type = source_type.lower().strip()
        
        # Map to standard types
        if source_type in ["arxiv", "pubmed", "journal", "paper", "academic"]:
            return "academic"
        elif source_type in ["web", "website", "webpage", "blog"]:
            return "web"
        elif source_type in ["news", "article", "media"]:
            return "news"
        elif source_type in ["document", "pdf", "doc", "txt"]:
            return "document"
        elif source_type in ["image", "photo", "picture", "graph"]:
            return "image"
        elif source_type in ["video", "movie", "clip"]:
            return "video"
        elif source_type in ["book", "ebook"]:
            return "book"
        else:
            return source_type

    def _ensure_required_fields(self, metadata: Dict) -> None:
        """Ensure required fields exist in metadata."""
        # Add missing required fields with default values
        if "title" not in metadata or not metadata["title"]:
            metadata["title"] = "Untitled Document"
        
        if "source" not in metadata or not metadata["source"]:
            metadata["source"] = "Unknown"
            
        if "source_type" not in metadata:
            metadata["source_type"] = "unknown"
            
        # Generate a timestamp if not present
        if "timestamp" not in metadata:
            from datetime import datetime
            metadata["timestamp"] = datetime.now().isoformat()

# Test the class when run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    standardizer = MetadataStandardizer()

    sample_metadata = [
        {"Title": "AI in Medicine", "Authors": "John Doe, Jane Smith", "DOI": "https://doi.org/10.1234/aimed", "URL": "  https://example.com  "},
        {"Paper Title": "Deep Learning", "Author": ["Alice Brown", "Bob White"], "doi": "10.5678/dl", "source_url": "https://example.com/deeplearning"}
    ]

    standardized_metadata = standardizer.standardize_metadata(sample_metadata)
    print("\n✅ Standardized Metadata:")
    for entry in standardized_metadata:
        print(entry)