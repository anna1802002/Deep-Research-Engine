# src/data_retrieval/orchestrator.py
import asyncio
from typing import List, Dict, Union, Optional
import os
import yaml
import logging

# Import clients for each data source
from src.data_retrieval.sources.arxiv import ArxivClient
from src.data_retrieval.sources.pubmed import PubMedClient
from src.data_retrieval.sources.google_scholar import GoogleScholarClient
from src.data_retrieval.sources.custom_search import CustomSearchClient

# Import preprocessor
from src.data_retrieval.preprocessor import DataPreprocessor

logger = logging.getLogger("deep_research.data_retrieval.orchestrator")

class DataRetrievalOrchestrator:
    """Orchestrates data retrieval from multiple research sources."""

    def __init__(self, config_path="config/settings.yaml"):
        """
        Initialize the orchestrator with configuration.
        
        Args:
            config_path: Path to settings configuration file
        """
        self.config = self._load_config(config_path)
        
        # Initialize original clients
        logger.info("Using legacy data source clients")
        self.arxiv_client = ArxivClient()
        self.pubmed_client = PubMedClient()
        self.google_scholar_client = GoogleScholarClient()
        self.custom_search_client = CustomSearchClient()
        
        # Initialize preprocessor
        self.preprocessor = DataPreprocessor()

    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from settings file.
        
        Args:
            config_path: Path to settings file
            
        Returns:
            Configuration dictionary
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
                return config.get("retrieval", {})
            else:
                logger.warning(f"Configuration file {config_path} not found, using defaults")
                return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}

    async def fetch_arxiv(self, query: str) -> List[Dict]:
        """Fetch research papers from ArXiv."""
        try:
            results = await asyncio.to_thread(self.arxiv_client.search, query)
            print(f"✅ ArXiv: Retrieved {len(results)} results")
            return results
        except Exception as e:
            print(f"⚠️ ArXiv search error: {e}")
            return []

    async def fetch_pubmed(self, query: str) -> List[Dict]:
        """Fetch research papers from PubMed."""
        try:
            results = await asyncio.to_thread(self.pubmed_client.search, query)
            print(f"✅ PubMed: Retrieved {len(results)} results")
            return results
        except Exception as e:
            print(f"⚠️ PubMed search error: {e}")
            return []

    async def fetch_google_scholar(self, query: str) -> List[Dict]:
        """Fetch research papers from Google Scholar."""
        try:
            results = await asyncio.to_thread(self.google_scholar_client.search, query)
            print(f"✅ Google Scholar: Retrieved {len(results)} results")
            return results
        except Exception as e:
            print(f"⚠️ Google Scholar search error: {e}")
            return []

    async def fetch_custom_search(self, query: str) -> List[Dict]:
        """Fetch research papers from Custom Search."""
        try:
            results = await asyncio.to_thread(self.custom_search_client.search, query)
            print(f"✅ Web Search: Retrieved {len(results)} results")
            return results
        except Exception as e:
            print(f"⚠️ Web search error: {e}")
            return []

    async def fetch_all_sources(self, query: str) -> List[Dict]:
        """
        Fetch data from all sources.
        
        Args:
            query: The search query
            
        Returns:
            Combined list of results from all sources
        """
        # Adjust query if needed to improve search results
        search_query = query if "quantum" in query.lower() or "," not in query else query.replace(",", " ")
        
        print(f"🔍 Searching for: {search_query}")
        
        # Use legacy clients
        results = await asyncio.gather(
            self.fetch_arxiv(search_query),
            self.fetch_pubmed(search_query),
            self.fetch_google_scholar(search_query),
            self.fetch_custom_search(search_query),
            return_exceptions=True  # Prevents failure from breaking execution
        )

        # Handle failures gracefully
        all_papers = []
        for i, result in enumerate(results):
            source_name = ["ArXiv", "PubMed", "Google Scholar", "Web Search"][i]
            
            if isinstance(result, Exception):
                print(f"⚠️ Error fetching data from {source_name}: {result}")
            elif isinstance(result, list):
                all_papers.extend(result)
            
        # Preprocess results
        processed_papers = self.preprocessor.preprocess(all_papers)
        
        print(f"🔎 Total unique results after preprocessing: {len(processed_papers)}")
        return processed_papers