# src/data_retrieval/web_fetcher.py

import requests
import time
import logging
import yaml
import os
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter, Retry
from src.data_retrieval.content_processor import ContentProcessor

logger = logging.getLogger("deep_research")

class WebFetcher:
    """Fetches and processes web content."""
    
    def __init__(self, timeout=10, max_retries=2, config_path="config/settings.yaml"):
        self.logger = logging.getLogger("deep_research.web_fetcher")
        self.timeout = timeout
        self.processor = ContentProcessor()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set up session with retries for direct web requests
        self.session = requests.Session()
        retries = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        
        # Set reasonable headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 Deep Research Engine/0.1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from settings file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
                return config.get("retrieval", {})
            else:
                self.logger.warning(f"Configuration file {config_path} not found, using defaults")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return {}
        
    def fetch_url(self, url):
        """Fetch and process content from a URL."""
        if not url or not url.startswith(('http://', 'https://')):
            self.logger.error(f"Invalid URL: {url}")
            return None
            
        try:
            self.logger.info(f"Fetching URL: {url}")
            start_time = time.time()
            
            # Extract domain for logging
            domain = urlparse(url).netloc
            
            # Direct fetch
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            
            # Check status
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                return None
                
            # Process content
            content = response.content
            processed = self.processor.process_content(content, url=url)
            
            # Log performance
            duration = time.time() - start_time
            self.logger.info(f"Fetched and processed {url} ({domain}) in {duration:.2f}s")
            
            return processed
            
        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout fetching {url}")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"Connection error fetching {url}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
            
    def fetch_multiple(self, urls, max_concurrent=5):
        """Fetch multiple URLs with basic concurrency control."""
        results = []
        
        # Simple batch processing to avoid overwhelming resources
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i+max_concurrent]
            
            for url in batch:
                result = self.fetch_url(url)
                if result:
                    results.append(result)
                    
            # Small delay between batches
            if i + max_concurrent < len(urls):
                time.sleep(1)
                
        return results