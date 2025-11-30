import re
import logging
from typing import List, Dict, Any, Union

logger = logging.getLogger("deep_research.metadata_processing.citation_extractor")

class CitationExtractor:
    """Extracts and standardizes citation information from metadata."""

    def __init__(self):
        """Define citation extraction patterns."""
        # Pattern for DOIs (Digital Object Identifiers)
        self.doi_pattern = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
        
        # Pattern for author names (more flexible to catch various formats)
        self.author_pattern = re.compile(r"([A-Z][a-z]+(?:[-'\s][A-Z][a-z]+)*)")
        
        # Pattern for title extraction
        self.title_pattern = re.compile(r"^(.*?)(?:\s\-\s|$)")
        
        # Pattern for year extraction
        self.year_pattern = re.compile(r"(?<!\d)(\d{4})(?!\d)")
        
        logger.info("CitationExtractor initialized")

    def extract_citations(self, metadata_list: List[Dict]) -> List[Dict]:
        """
        Extract citations from a given metadata list.
        
        Args:
            metadata_list: List of metadata dictionaries
            
        Returns:
            List of citation dictionaries
        """
        if not metadata_list:
            logger.warning("Empty metadata list provided for citation extraction")
            return []
            
        extracted_citations = []
        
        for i, metadata in enumerate(metadata_list):
            try:
                if not metadata:
                    logger.warning(f"Empty metadata entry at index {i}, skipping")
                    continue
                    
                citation = {
                    "title": self.extract_title(metadata.get("title", "")),
                    "authors": self.extract_authors(metadata.get("authors", "")),
                    "doi": self.extract_doi(metadata.get("doi", "")),
                    "journal": metadata.get("journal", metadata.get("source", "Unknown")),
                    "url": metadata.get("url", ""),
                    "year": self.extract_year(metadata.get("publication_date", ""))
                }
                
                # Add additional fields if available
                if "arxiv_id" in metadata:
                    citation["arxiv_id"] = metadata["arxiv_id"]
                    
                if "abstract" in metadata:
                    citation["abstract"] = metadata["abstract"]
                    
                if "source_type" in metadata:
                    citation["source_type"] = metadata["source_type"]
                    
                extracted_citations.append(citation)
                
            except Exception as e:
                logger.error(f"Error extracting citation from metadata at index {i}: {e}")
                # Add a minimal citation to avoid breaking dependent code
                extracted_citations.append({
                    "title": metadata.get("title", "Unknown Title"),
                    "authors": [],
                    "doi": "No DOI Found",
                    "journal": "Unknown",
                    "error": str(e)
                })

        logger.info(f"Extracted {len(extracted_citations)} citations from metadata")
        return extracted_citations

    def extract_doi(self, doi_text: Union[str, Any]) -> str:
        """
        Extract DOI if present in the text.
        
        Args:
            doi_text: Text that may contain a DOI
            
        Returns:
            Extracted DOI or "No DOI Found"
        """
        if not doi_text:
            return "No DOI Found"
            
        # Convert to string if not already
        if not isinstance(doi_text, str):
            doi_text = str(doi_text)
            
        # Clean up DOI by removing common prefixes
        doi_text = doi_text.strip()
        if doi_text.startswith("https://doi.org/"):
            doi_text = doi_text.replace("https://doi.org/", "")
        elif doi_text.startswith("http://doi.org/"):
            doi_text = doi_text.replace("http://doi.org/", "")
        elif doi_text.startswith("doi:"):
            doi_text = doi_text.replace("doi:", "")
            
        # Search for DOI pattern
        match = self.doi_pattern.search(doi_text)
        return match.group(0) if match else "No DOI Found"

    def extract_authors(self, author_text: Any) -> List[str]:
        """
        Extract authors as a list from text.
        
        Args:
            author_text: Author information as string, list, or other format
            
        Returns:
            List of author names
        """
        if not author_text:
            return []
            
        if isinstance(author_text, str):
            # First try splitting by common separators if the string contains them
            if any(sep in author_text for sep in [',', ';', ' and ']):
                # Split by common separators
                authors = []
                for author in re.split(r',|;|\s+and\s+', author_text):
                    author = author.strip()
                    if author:
                        authors.append(author)
                return authors
            
            # If no common separators or failed to extract, try regex pattern
            authors = self.author_pattern.findall(author_text)
            if authors:
                return authors
            
            # If all else fails, return the whole string as a single author
            return [author_text.strip()]
            
        elif isinstance(author_text, list):
            # Clean each entry in the list
            return [str(author).strip() for author in author_text if author]
        
        # Try to convert to string for anything else
        try:
            return [str(author_text).strip()]
        except:
            return []

    def extract_title(self, title_text: Union[str, Any]) -> str:
        """
        Extract and clean the title from citation text.
        
        Args:
            title_text: Text containing the title
            
        Returns:
            Cleaned title text
        """
        if not title_text:
            return ""
            
        # Convert to string if not already
        if not isinstance(title_text, str):
            title_text = str(title_text)
            
        # Clean the title
        title_text = title_text.strip()
        
        # Extract using pattern
        match = self.title_pattern.match(title_text)
        title = match.group(1) if match else title_text
        
        # Remove unnecessary whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
        
    def extract_year(self, date_text: Union[str, Any]) -> str:
        """
        Extract year from a date string.
        
        Args:
            date_text: Date string that may contain a year
            
        Returns:
            Extracted year or empty string
        """
        if not date_text:
            return ""
            
        # Convert to string if not already
        if not isinstance(date_text, str):
            date_text = str(date_text)
            
        # Extract using pattern
        match = self.year_pattern.search(date_text)
        return match.group(1) if match else ""
        
    def format_citation(self, citation: Dict, style: str = "apa") -> str:
        """
        Format a citation according to a specific style.
        
        Args:
            citation: Citation dictionary
            style: Citation style ("apa", "mla", "chicago")
            
        Returns:
            Formatted citation string
        """
        if not citation:
            return ""
            
        title = citation.get("title", "")
        authors = citation.get("authors", [])
        year = citation.get("year", "")
        journal = citation.get("journal", "")
        doi = citation.get("doi", "")
        url = citation.get("url", "")
        
        if style == "apa":
            # APA style
            author_text = ", ".join(authors[:-1])
            if len(authors) > 1:
                author_text += f", & {authors[-1]}"
            elif authors:
                author_text = authors[0]
            else:
                author_text = "Unknown Author"
                
            citation_text = f"{author_text}"
            
            if year:
                citation_text += f" ({year})."
            else:
                citation_text += "."
                
            if title:
                citation_text += f" {title}."
                
            if journal:
                citation_text += f" {journal},"
                
            if doi != "No DOI Found":
                citation_text += f" DOI: {doi}"
            elif url:
                citation_text += f" Retrieved from {url}"
                
            return citation_text
            
        elif style == "mla":
            # MLA style
            author_text = ", ".join(authors[:-1])
            if len(authors) > 1:
                author_text += f", and {authors[-1]}"
            elif authors:
                author_text = authors[0]
            else:
                author_text = "Unknown Author"
                
            citation_text = f"{author_text}."
            
            if title:
                citation_text += f" \"{title}.\""
                
            if journal:
                citation_text += f" {journal},"
                
            if year:
                citation_text += f" {year}."
                
            if url:
                citation_text += f" {url}."
                
            return citation_text
            
        else:
            # Default to simple format
            parts = []
            
            if authors:
                parts.append(", ".join(authors))
                
            if title:
                parts.append(f"\"{title}\"")
                
            if journal:
                parts.append(journal)
                
            if year:
                parts.append(year)
                
            if doi != "No DOI Found":
                parts.append(f"DOI: {doi}")
            elif url:
                parts.append(f"URL: {url}")
                
            return ". ".join(parts)

# Test the CitationExtractor
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    extractor = CitationExtractor()

    sample_metadata = [
        {
            "title": "AI for Medicine - A Review", 
            "authors": "John Doe, Jane Smith", 
            "doi": "https://doi.org/10.1234/aimed", 
            "journal": "Medical AI Journal",
            "publication_date": "2023-05-15"
        },
        {
            "title": "Deep Learning in Healthcare", 
            "authors": ["Alice Brown", "Bob White"], 
            "doi": "10.5678/dl", 
            "journal": "AI Healthcare Journal",
            "publication_date": "2022"
        }
    ]

    extracted_citations = extractor.extract_citations(sample_metadata)

    print("\n✅ Extracted Citations:")
    for citation in extracted_citations:
        print(citation)
        
    print("\n✅ Formatted Citations (APA):")
    for citation in extracted_citations:
        print(extractor.format_citation(citation, "apa"))