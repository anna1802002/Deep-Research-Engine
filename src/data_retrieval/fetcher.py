import requests
import time
import random
from requests.adapters import HTTPAdapter, Retry
from typing import Dict, List

# Import API Clients
from src.data_retrieval.sources.arxiv import ArxivClient
from src.data_retrieval.sources.pubmed import PubMedClient
from src.data_retrieval.sources.google_scholar import GoogleScholarClient
from src.data_retrieval.sources.custom_search import CustomSearchClient

# Import content processor with chunking capabilities
from src.data_retrieval.content_processor import ContentProcessor

class Fetcher:
    """Handles fetching research data from multiple sources with retries and rate limiting."""

    def __init__(self, rate_limit=1.5, max_retries=3, backoff_factor=1, chunk_size=1000, chunk_overlap=100):
        """
        Initialize Fetcher with:
        - `rate_limit`: Delay (in seconds) between API calls to prevent overload.
        - `max_retries`: Number of retry attempts for failed API calls.
        - `backoff_factor`: Exponential delay factor for retries.
        - `chunk_size`: Size of content chunks.
        - `chunk_overlap`: Overlap between chunks.
        """
        self.rate_limit = rate_limit
        self.session = requests.Session()
        retries = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        # Initialize API Clients
        self.arxiv_client = ArxivClient()
        self.pubmed_client = PubMedClient()
        self.google_scholar_client = GoogleScholarClient()
        self.custom_search_client = CustomSearchClient()
        
        # Initialize content processor with chunking capabilities
        self.content_processor = ContentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def fetch_arxiv(self, query: str, max_results: int = 5) -> List[Dict]:
        """Fetch results from ArXiv."""
        print("🔍 Fetching ArXiv results...")
        return self.arxiv_client.search(query, max_results)

    def fetch_pubmed(self, query: str, max_results: int = 5) -> List[Dict]:
        """Fetch results from PubMed."""
        print("🔍 Fetching PubMed results...")
        return self.pubmed_client.search(query, max_results)

    def fetch_google_scholar(self, query: str, max_results: int = 5) -> List[Dict]:
        """Fetch results from Google Scholar."""
        print("🔍 Fetching Google Scholar results...")
        return self.google_scholar_client.search(query, max_results)

    def fetch_custom_search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Fetch results from Google Custom Search."""
        print("🔍 Fetching Custom Search results...")
        return self.custom_search_client.search(query, max_results)

    def fetch_all_sources(self, query: str, max_results: int = 5) -> List[Dict]:
        """Fetch results from all sources while avoiding duplicate entries."""
        print(f"🔎 Searching across all academic sources for: {query}")

        # Fetch results from all sources
        sources = [
            self.fetch_arxiv(query, max_results),
            self.fetch_pubmed(query, max_results),
            self.fetch_google_scholar(query, max_results),
            self.fetch_custom_search(query, max_results),
        ]

        # Introduce a delay to respect API rate limits
        time.sleep(self.rate_limit + random.uniform(0, 0.5))

        # Process results and remove duplicates
        all_results = []
        seen_titles = set()

        for source_results in sources:
            for paper in source_results:
                title = paper["title"].strip().lower()
                if title not in seen_titles:
                    seen_titles.add(title)
                    
                    # If the paper has content, process and chunk it
                    if "content" in paper and paper["content"]:
                        processed = self.content_processor.process_content(
                            paper["content"], 
                            url=paper.get("url"),
                            source_type=paper.get("source", "academic")
                        )
                        
                        # Add processed content and chunks to the paper
                        if processed:
                            paper["processed_text"] = processed.get("text", "")
                            paper["chunks"] = processed.get("chunks", [])
                    
                    all_results.append(paper)

        return all_results

    def fetch_and_process_url(self, url: str) -> Dict:
        """Fetch and process content from a specific URL."""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                # Process the content
                processed = self.content_processor.process_content(
                    response.content,
                    url=url,
                    source_type="web"
                )
                
                return processed
            else:
                print(f"Failed to fetch {url}: Status code {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

if __name__ == "__main__":
    fetcher = Fetcher(rate_limit=2)  # Set rate limit for API calls
    user_query = input("Enter your research query: ")
    
    research_papers = fetcher.fetch_all_sources(user_query, max_results=5)

    if research_papers:
        print("\n🔹 Research Papers Found:")
        for paper in research_papers:
            print(f" - {paper['title']} ({paper['url']})")
            
            # Display chunk information if available
            if "chunks" in paper and paper["chunks"]:
                print(f"   Processed into {len(paper['chunks'])} chunks")
    else:
        print("⚠️ No results found. Try a different query.")