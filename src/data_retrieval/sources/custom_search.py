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

        return self._parse_response(response.json(), max_results)

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

if __name__ == "__main__":
    client = CustomSearchClient()
    user_query = input("Enter your search query: ")
    search_results = client.search(user_query, max_results=25)  # Ensure 25 results are requested

    if search_results:
        print("\n🔍 Top Web Search Results:")
        for result in search_results:
            print(f" - {result['title']} ({result['url']})")
    else:
        print("⚠️ No results found.")
