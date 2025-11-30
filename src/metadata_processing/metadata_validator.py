import re
from datetime import datetime
from typing import Dict, List, Any, Union
import logging

logger = logging.getLogger("deep_research.metadata_processing.validator")

class MetadataValidator:
    """Validates metadata for completeness and correctness."""

    def validate(self, metadata: Dict) -> Dict:
        """
        Validate metadata and return updated version with validation status.
        
        Args:
            metadata: Dictionary of metadata to validate
            
        Returns:
            Dictionary with validated metadata and validation status
        """
        if not metadata:
            logger.warning("Empty metadata provided for validation")
            return {
                "_validation": {
                    "valid": False,
                    "issues": ["Empty metadata"],
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        # Make a copy to avoid modifying original
        validated = metadata.copy()
        issues = []
        
        # Check required fields
        for field in ["title", "source"]:
            if field not in validated or not validated[field]:
                issues.append(f"Missing required field: {field}")
                validated[field] = "Unknown" if field == "title" else "Unspecified"
        
        # Validate URL
        if "url" in validated and validated["url"]:
            url = validated["url"]
            if not url.startswith(("http://", "https://")):
                issues.append("Invalid URL format")
                validated["url"] = f"https://{url}" if not url.startswith("www.") else f"https://{url}"
        else:
            issues.append("Missing URL")
            validated["url"] = ""
        
        # Validate date format
        if "publication_date" in validated and validated["publication_date"]:
            # Try to parse and normalize the date
            normalized_date = self._normalize_date(validated["publication_date"])
            if normalized_date:
                validated["publication_date"] = normalized_date
            else:
                issues.append("Invalid date format")
                validated["publication_date"] = ""
        
        # Validate authors
        if "authors" in validated and validated["authors"]:
            validated["authors"] = self._normalize_authors(validated["authors"])
            if not validated["authors"]:
                issues.append("Invalid authors format")
        
        # Validate DOI if present
        if "doi" in validated and validated["doi"]:
            if not self._validate_doi(validated["doi"]):
                issues.append("Invalid DOI format")
        
        # Check content fields
        if "abstract" not in validated or not validated.get("abstract"):
            issues.append("Missing abstract")
        
        # Add validation metadata
        validated["_validation"] = {
            "valid": len(issues) == 0,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Validated metadata with {len(issues)} issues")
        return validated
    
    def validate_batch(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        Validate a batch of metadata entries.
        
        Args:
            metadata_list: List of metadata dictionaries
            
        Returns:
            List of validated metadata dictionaries
        """
        if not metadata_list:
            logger.warning("Empty metadata list provided for batch validation")
            return []
            
        validated_list = []
        
        for metadata in metadata_list:
            validated = self.validate(metadata)
            validated_list.append(validated)
            
        return validated_list
    
    def _normalize_date(self, date_str: Union[str, Any]) -> str:
        """
        Normalize dates to ISO format (YYYY-MM-DD).
        
        Args:
            date_str: Date string to normalize
            
        Returns:
            Normalized date string or empty string if invalid
        """
        if not date_str:
            return ""
            
        if not isinstance(date_str, str):
            date_str = str(date_str)
            
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
                
        return ""  # Return empty string if parsing fails
        
    def _normalize_authors(self, authors: Any) -> List[str]:
        """
        Normalize authors list to consistent format.
        
        Args:
            authors: Authors input in various formats
            
        Returns:
            List of author names as strings
        """
        if isinstance(authors, str):
            # Split by common separators
            return [a.strip() for a in re.split(r',|;|and', authors) if a.strip()]
        elif isinstance(authors, list):
            return [a.strip() if isinstance(a, str) else str(a) for a in authors if a]
        return []
        
    def _validate_doi(self, doi: str) -> bool:
        """
        Validate DOI format.
        
        Args:
            doi: DOI string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not doi:
            return False
            
        # Basic DOI format validation
        # DOIs typically follow the pattern 10.XXXX/YYYY
        doi_pattern = re.compile(r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$', re.IGNORECASE)
        
        # Clean DOI first
        cleaned_doi = doi.strip()
        if cleaned_doi.startswith("https://doi.org/"):
            cleaned_doi = cleaned_doi.replace("https://doi.org/", "")
        elif cleaned_doi.startswith("http://doi.org/"):
            cleaned_doi = cleaned_doi.replace("http://doi.org/", "")
        elif cleaned_doi.startswith("doi:"):
            cleaned_doi = cleaned_doi.replace("doi:", "")
            
        return bool(doi_pattern.match(cleaned_doi))

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    validator = MetadataValidator()
    
    # Test with sample data
    sample_metadata = {
        "title": "AI for Medicine - A Review",
        "authors": "John Doe, Jane Smith",
        "doi": "https://doi.org/10.1234/aimed",
        "publication_date": "2024-02-15",
        "abstract": "This paper discusses the latest AI applications in healthcare.",
        "source": "arXiv",
        "url": "https://arxiv.org/abs/1234.5678"
    }
    
    validated = validator.validate(sample_metadata)
    print("\n✅ Validation Result:")
    print(f"Valid: {validated['_validation']['valid']}")
    print(f"Issues: {validated['_validation']['issues']}")
    print("Validated metadata:", validated)