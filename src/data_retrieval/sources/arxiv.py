# src/data_retrieval/sources/arxiv.py (updated)
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict
import time

class ArxivClient:
    BASE_URL = "http://export.arxiv.org/api/query"

    def search(self, query: str, max_results: int = 25) -> List[Dict]:
        """Search ArXiv for relevant papers with retries."""
        formatted_query = "+".join(query.split())  
        url = f"{self.BASE_URL}?search_query=all:{formatted_query}&start=0&max_results={max_results}"

        retries = 3  # Number of retry attempts
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=10)  # Added timeout to prevent hangs

                if response.status_code == 200:
                    results = self._parse_arxiv_response(response.text)
                    # Add source field to each result
                    for result in results:
                        result['source'] = 'ArXiv'
                    return results
                else:
                    print(f"⚠️ ArXiv API returned {response.status_code}, retrying...")
                    time.sleep(2)  # Wait before retrying

            except requests.ConnectionError as e:
                print(f"🔴 Connection error: {e}, retrying ({attempt+1}/{retries})...")
                time.sleep(2)  # Wait before retrying

        print("❌ Failed to retrieve data from ArXiv after multiple attempts.")
        return []

    def _parse_arxiv_response(self, xml_data: str) -> List[Dict]:
        """Parse ArXiv API XML response into a structured JSON format."""
        root = ET.fromstring(xml_data)

        results = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
            summary = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
            link = entry.find("{http://www.w3.org/2005/Atom}id").text.strip()

            results.append({"title": title, "summary": summary, "url": link})

        return results

# src/data_retrieval/sources/pubmed.py (updated)
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict

class PubMedClient:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def search(self, query: str, max_results: int = 25) -> List[Dict]:
        """Search PubMed for relevant papers and return their details."""
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "xml",
            "retmax": max_results
        }
        response = requests.get(self.BASE_URL, params=params)

        if response.status_code != 200:
            print(f"🔴 Error: PubMed API returned {response.status_code}")
            return []

        results = self._fetch_paper_details(response.text)
        # Add source field to each result
        for result in results:
            result['source'] = 'PubMed'
        return results

    def _fetch_paper_details(self, xml_data: str) -> List[Dict]:
        """Extract paper IDs and fetch details from PubMed."""
        root = ET.fromstring(xml_data)
        id_list = [id_elem.text for id_elem in root.findall(".//Id")]

        if not id_list:
            return []

        # Fetch details of the papers
        params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml"
        }
        response = requests.get(self.FETCH_URL, params=params)

        if response.status_code != 200:
            print(f"🔴 Error: Failed to fetch PubMed details ({response.status_code})")
            return []

        return self._parse_pubmed_response(response.text)

    def _parse_pubmed_response(self, xml_data: str) -> List[Dict]:
        """Parse PubMed XML response into structured results."""
        root = ET.fromstring(xml_data)
        results = []

        for article in root.findall(".//PubmedArticle"):
            title_elem = article.find(".//ArticleTitle")
            abstract_elem = article.find(".//AbstractText")
            pmid_elem = article.find(".//PMID")

            title = title_elem.text if title_elem is not None else "No title available"
            abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
            pmid = pmid_elem.text if pmid_elem is not None else "N/A"
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}"

            results.append({
                "title": title,
                "summary": abstract,
                "url": url
            })

        return results

# src/data_retrieval/sources/google_scholar.py (updated)
import requests
import yaml
import os
from typing import List, Dict

class GoogleScholarClient:
    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, config_path="config/api_keys.yaml"):
        self.api_key, self.cse_id = self._load_api_credentials(config_path)

    def _load_api_credentials(self, config_path: str):
        """Load API key and Custom Search Engine ID from config."""
        if not os.path.exists(config_path):
            raise ValueError(f"⚠️ Config file not found: {config_path}")

        try:
            with open(config_path, "r") as file:
                config = yaml.safe_load(file)
                return config.get("GOOGLE_SCHOLAR_API_KEY"), config.get("GOOGLE_SCHOLAR_CX")
        except Exception as e:
            raise ValueError(f"⚠️ Error loading API credentials: {e}")

    def search(self, query: str, max_results: int = 25) -> List[Dict]:
        """Search Google Scholar using Custom Search API."""
        if not self.api_key or not self.cse_id:
            print("⚠️ Google API key or CSE ID missing. Check config/api_keys.yaml")
            return []

        params = {
            "q": query,
            "cx": self.cse_id,
            "key": self.api_key,
            "num": max_results
        }
        response = requests.get(self.BASE_URL, params=params)

        if response.status_code != 200:
            print(f"🔴 Error: Google Custom Search API returned {response.status_code}")
            return []

        results = self._parse_response(response.json(), max_results)
        # Add source field to each result
        for result in results:
            result['source'] = 'Google Scholar'
        return results

    def _parse_response(self, json_data: Dict, max_results: int) -> List[Dict]:
        """Extract relevant details from Google Scholar search results."""
        results = []
        for item in json_data.get("items", []):
            results.append({
                "title": item.get("title", "No title"),
                "snippet": item.get("snippet", "No summary available"),
                "url": item.get("link", "No link available"),
            })

        return results[:max_results] if len(results) >= max_results else results

# src/data_retrieval/sources/custom_search.py (updated)
import requests
import yaml
from typing import List, Dict

class CustomSearchClient:
    def __init__(self, config_path="config/api_keys.yaml"):
        self.api_key, self.cse_id = self._load_api_key(config_path)
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def _load_api_key(self, config_path: str):
        """Load Google API key and CSE ID from the config file."""
        try:
            with open(config_path, "r") as file:
                config = yaml.safe_load(file)
                api_key = config.get("GOOGLE_API_KEY", None)  # Replace with your actual key name
                cse_id = config.get("GOOGLE_CSE_ID", None)  # Ensure you have a CSE ID
                return api_key, cse_id
        except Exception as e:
            print(f"🔴 Error loading API key: {e}")
            return None, None

    def search(self, query: str, max_results: int = 25) -> List[Dict]:
        """Perform a Google Custom Search using the API key and CSE ID."""
        if not self.api_key or not self.cse_id:
            print("⚠️ Google API key or CSE ID is missing. Check config/api_keys.yaml")
            return []

        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": max_results  # Ensure it requests the desired number of results
        }

        response = requests.get(self.base_url, params=params)

        if response.status_code != 200:
            print(f"🔴 Error: Google Custom Search API returned {response.status_code}")
            return []

        results = self._parse_response(response.json(), max_results)
        # Add source field to each result
        for result in results:
            result['source'] = 'Web Search'
        return results

    def _parse_response(self, data: Dict, max_results: int) -> List[Dict]:
        """Parse the Google Custom Search API response and extract relevant results."""
        results = []
        for result in data.get("items", []):
            title = result.get("title", "No title")
            link = result.get("link", "#")
            snippet = result.get("snippet", "No description available")
            results.append({"title": title, "url": link, "snippet": snippet})

        # Ensure exactly max_results are returned
        return results[:max_results] if len(results) >= max_results else results