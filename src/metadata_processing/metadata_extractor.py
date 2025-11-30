import re
from datetime import datetime
from urllib.parse import urlparse
import logging

logger = logging.getLogger("deep_research.metadata_processing.extractor")

class MetadataExtractor:
    """Extracts metadata from different source types."""
    
    def extract_metadata(self, content, source_type):
        """Extract metadata based on source type."""
        logger.info(f"Extracting metadata from source type: {source_type}")
        
        if source_type == "arxiv":
            return self._extract_arxiv_metadata(content)
        elif source_type == "pubmed":
            return self._extract_pubmed_metadata(content)
        elif source_type == "web":
            return self._extract_web_metadata(content)
        else:
            return self._extract_general_metadata(content)
    
    def _extract_arxiv_metadata(self, content):
        """Extract ArXiv specific metadata."""
        metadata = {}
        
        # Extract title
        if "title" in content:
            metadata["title"] = content["title"]
        
        # Extract authors
        if "authors" in content:
            metadata["authors"] = self._normalize_authors(content["authors"])
        
        # Extract publication date
        if "published" in content:
            metadata["publication_date"] = self._normalize_date(content["published"])
        elif "year" in content:
            metadata["publication_date"] = self._normalize_date(str(content["year"]))
        
        # Extract URL and ID
        if "id" in content:
            metadata["url"] = content["id"]
            metadata["arxiv_id"] = content["id"].split("/")[-1]
        elif "url" in content:
            metadata["url"] = content["url"]
            # Try to extract arxiv ID from URL
            id_match = re.search(r'abs/([^/]+)$', content["url"])
            if id_match:
                metadata["arxiv_id"] = id_match.group(1)
        
        # Extract categories/tags
        if "categories" in content:
            metadata["categories"] = content["categories"]
        
        # Extract abstract if available
        if "abstract" in content:
            metadata["abstract"] = content["abstract"]
        
        # Set source and type
        metadata["source"] = "arXiv"
        metadata["source_type"] = "academic"
        
        # Extract PDF URL if present
        if "pdf_url" in content:
            metadata["pdf_url"] = content["pdf_url"]
        
        return metadata
        
    def _extract_pubmed_metadata(self, content):
        """Extract PubMed specific metadata."""
        metadata = {}
        
        # Extract title
        if "title" in content:
            metadata["title"] = content["title"]
        
        # Extract authors
        if "authors" in content:
            metadata["authors"] = self._normalize_authors(content["authors"])
        
        # Extract publication date
        if "publication_date" in content:
            metadata["publication_date"] = self._normalize_date(content["publication_date"])
        elif "year" in content:
            metadata["publication_date"] = self._normalize_date(str(content["year"]))
        
        # Extract DOI
        if "doi" in content:
            metadata["doi"] = content["doi"]
        
        # Extract PMID
        if "pmid" in content:
            metadata["pmid"] = content["pmid"]
        
        # Extract abstract
        if "abstract" in content:
            metadata["abstract"] = content["abstract"]
        
        # Extract URL
        if "url" in content:
            metadata["url"] = content["url"]
        
        # Set source
        metadata["source"] = "PubMed"
        metadata["source_type"] = "academic"
        
        return metadata
    
    def _extract_web_metadata(self, content):
        """Extract web content metadata."""
        metadata = {}
        
        # Extract domain
        if "url" in content:
            try:
                parsed_url = urlparse(content["url"])
                metadata["domain"] = parsed_url.netloc
            except:
                metadata["domain"] = "unknown"
        
        # Extract title
        if "title" in content:
            metadata["title"] = content["title"]
        
        # Extract published date if available
        if "published_date" in content:
            metadata["publication_date"] = self._normalize_date(content["published_date"])
        elif "year" in content:
            metadata["publication_date"] = self._normalize_date(str(content["year"]))
        
        # Extract authors if available
        if "authors" in content:
            metadata["authors"] = self._normalize_authors(content["authors"])
        
        # Set source
        metadata["source"] = "Web"
        metadata["source_type"] = "web"
        
        # Extract content type if available
        if "content_type" in content:
            metadata["content_type"] = content["content_type"]
        
        return metadata
    
    def _extract_general_metadata(self, content):
        """Extract general metadata for unknown sources."""
        metadata = {}
        
        # Try to extract as many fields as possible
        for field in ["title", "authors", "publication_date", "url", "abstract", "content", "source_type", "year"]:
            if field in content:
                if field == "authors":
                    metadata[field] = self._normalize_authors(content[field])
                elif field == "publication_date" or field == "year":
                    metadata["publication_date"] = self._normalize_date(str(content[field]))
                else:
                    metadata[field] = content[field]
        
        # Extract content type if available
        if "content_type" in content:
            metadata["content_type"] = content["content_type"]
        elif "type" in content:
            metadata["content_type"] = content["type"]
        
        # Set source if available, otherwise unknown
        metadata["source"] = content.get("source", "Unknown")
        
        # If source_type not already set
        if "source_type" not in metadata:
            metadata["source_type"] = content.get("source_type", "unknown")
        
        return metadata
    
    def _normalize_authors(self, authors):
        """Normalize author names to a consistent format."""
        if isinstance(authors, str):
            # Split by common separators
            return [a.strip() for a in re.split(r',|;|and', authors) if a.strip()]
        elif isinstance(authors, list):
            return [a.strip() if isinstance(a, str) else a for a in authors]
        return []
    
    def _normalize_date(self, date_str):
        """Normalize dates to ISO format (YYYY-MM-DD)."""
        if not date_str:
            return ""
            
        # Try different date formats
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
                
        # Try to extract year if full date parsing fails
        year_match = re.search(r'(?<!\d)(\d{4})(?!\d)', date_str)
        if year_match:
            return f"{year_match.group(1)}-01-01"  # Default to January 1st
                
        return date_str 