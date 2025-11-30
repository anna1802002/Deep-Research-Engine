import sys
import os

# Ensure the project root directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import academic source clients
from src.data_retrieval.sources.arxiv import ArxivClient
from src.data_retrieval.sources.google_scholar import GoogleScholarClient
from src.data_retrieval.sources.pubmed import PubMedClient
from typing import List, Dict


class AcademicSource:
    """Handles retrieval of academic papers from multiple sources."""
    
    def __init__(self):
        self.arxiv_client = ArxivClient()
        self.google_scholar_client = GoogleScholarClient()
        self.pubmed_client = PubMedClient()

    def search_academic_sources(self, query: str, max_results: int = 25) -> Dict[str, List[Dict]]:
        """Fetch research papers from ArXiv, Google Scholar, and PubMed."""
        results = {
            "arxiv": self.arxiv_client.search(query, max_results),
            "google_scholar": self.google_scholar_client.search(query, max_results),
            "pubmed": self.pubmed_client.search(query, max_results),
        }
        return results


if __name__ == "__main__":
    academic_source = AcademicSource()
    user_query = input("Enter your research topic: ")

    papers = academic_source.search_academic_sources(user_query)

    print("\n🔹 **Academic Research Results** 🔹")

    for source, results in papers.items():
        print(f"\n📌 **{source.upper()} Results:**")
        if results:
            for idx, paper in enumerate(results, 1):
                print(f" {idx}. {paper['title']} ({paper['url']})")
        else:
            print("⚠️ No results found.")
