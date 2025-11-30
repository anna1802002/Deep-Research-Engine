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

        return self._fetch_paper_details(response.text)

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

if __name__ == "__main__":
    client = PubMedClient()
    user_query = input("Enter your research topic: ")
    papers = client.search(user_query)

    if papers:
        print("\n🔹 Top PubMed Papers:")
        for paper in papers:
            print(f" - {paper['title']} ({paper['url']})")
    else:
        print("⚠️ No results found. Try a different query.")
