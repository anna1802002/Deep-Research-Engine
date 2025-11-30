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

        all_results = []
        start_index = 1  # Start from the first result
        while len(all_results) < max_results:
            params = {
                "q": query,
                "cx": self.cse_id,
                "key": self.api_key,
                "num": min(10, max_results - len(all_results)),  # Fetch up to 10 per request
                "start": start_index  # Start index for pagination
            }
            response = requests.get(self.BASE_URL, params=params)

            if response.status_code != 200:
                print(f"🔴 Error: Google Custom Search API returned {response.status_code}")
                break  # Exit loop if request fails

            new_results = self._parse_response(response.json())
            if not new_results:
                break  # Stop if no more results
            
            all_results.extend(new_results)
            start_index += len(new_results)  # Move to the next batch
        
        # Add source field to each result
        for result in all_results:
            result['source'] = 'Google Scholar'
            
        return all_results[:max_results]  # Ensure exactly `max_results`

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

if __name__ == "__main__":
    client = GoogleScholarClient()
    user_query = input("Enter your research topic: ")
    papers = client.search(user_query, max_results=25)

    if papers:
        print("\n🔹 Top Google Scholar Papers:")
        for paper in papers:
            print(f" - {paper['title']} ({paper['url']})")
    else:
        print("⚠️ No results found. Try a different query.")
