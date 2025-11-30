# src/data_retrieval/preprocessor.py (updated)
import re
from typing import List, Dict

class DataPreprocessor:
    """Preprocesses research data by cleaning, normalizing, and removing duplicates."""

    def __init__(self):
        self.seen_titles = set()  # Track duplicate titles
        
    def clean_text(self, text: str) -> str:
        """Remove unnecessary spaces and special characters."""
        if not text:
            return ""
            
        text = text.strip()
        text = re.sub(r"\s+", " ", text)  # Replace multiple spaces with single space
        text = re.sub(r"[^\w\s.,;:()\-'\"]", "", text)  # Remove special characters while keeping common punctuation
        return text

    def normalize_entry(self, entry: Dict) -> Dict:
        """Normalize a single research entry."""
        # Extract title and clean it
        title = self.clean_text(entry.get("title", "No title available"))
        
        # Determine the summary field (different sources use different field names)
        summary = entry.get("summary", entry.get("snippet", "No summary available"))
        summary = self.clean_text(summary)
        
        # Ensure URL is available
        url = entry.get("url", "#")
        
        # Get source or set a default
        source = entry.get("source", "Unknown")
        
        # Create normalized entry
        return {
            "title": title,
            "summary": summary,
            "url": url,
            "source": source
        }

    def remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate research papers based on titles."""
        unique_results = []
        # Reset seen titles for new batch
        self.seen_titles = set()
        
        for entry in results:
            # Get a cleaned, lowercase title for comparison
            title = entry["title"].lower()
            
            # Consider approximate duplicates by using only the first 50 chars
            title_start = title[:50] if len(title) > 50 else title
            
            if title_start not in self.seen_titles:
                self.seen_titles.add(title_start)
                unique_results.append(entry)
                
        return unique_results

    def filter_relevance(self, results: List[Dict], query: str) -> List[Dict]:
        """Filter results by relevance to the query terms."""
        if not query or not results:
            return results
            
        # Extract key terms from the query
        query_terms = set(re.findall(r'\w+', query.lower()))
        
        # Filter out non-relevant results
        relevant_results = []
        for entry in results:
            title = entry["title"].lower()
            summary = entry["summary"].lower()
            
            # Check if any query term is in the title or summary
            is_relevant = any(term in title or term in summary for term in query_terms)
            
            if is_relevant:
                relevant_results.append(entry)
                
        # If filtering removed too many results, return the original list
        if len(relevant_results) < len(results) / 2:
            return results
            
        return relevant_results

    def preprocess(self, raw_data: List[Dict], query: str = "") -> List[Dict]:
        """Clean, normalize, filter, and deduplicate research results."""
        if not raw_data:
            return []
            
        # Normalize data
        cleaned_data = [self.normalize_entry(entry) for entry in raw_data if entry]
        
        # Remove duplicates
        unique_data = self.remove_duplicates(cleaned_data)
        
        # Filter by relevance if query is provided
        if query:
            filtered_data = self.filter_relevance(unique_data, query)
        else:
            filtered_data = unique_data
            
        return filtered_data