#server.py
"""
Enhanced MCP Server for arXiv Paper Search

This server implements the paper search functionality while supporting
both MCP protocol and direct execution mode.
"""

import os
import requests
import re
import hashlib
from pathlib import Path
import json
import time
import argparse
import sys
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("arxiv-mcp-server")

# Try to import MCP if available
try:
    from mcp.server.fastmcp import FastMCP
    HAS_MCP = True
except ImportError:
    logger.warning("MCP package not found. Running in standalone mode only.")
    HAS_MCP = False

# API configuration
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
USER_AGENT = "PaperSearch/1.0 (mailto:research@example.com)"  # Update with your email

# Configuration
REQUEST_DELAY = 3.0
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
DEFAULT_MAX_RESULTS = 10

# Cache directory
CACHE_DIR = Path("paper_cache")
CACHE_DIR.mkdir(exist_ok=True)

# Modified section of server.py - Focus on reliability rather than query processing

def safe_request(url, params=None, timeout=REQUEST_TIMEOUT):
    """Make a request with error handling and retries"""
    retries = MAX_RETRIES
    base_delay = 2  # seconds
    
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Requesting {url} with {params} (attempt {attempt}/{retries})")
            response = requests.get(
                url, 
                params=params, 
                headers={"User-Agent": USER_AGENT}, 
                timeout=timeout
            )
            
            # Check for rate limiting responses
            if response.status_code == 503:
                # Extract retry time from headers
                retry_after = int(response.headers.get("retry-after", 30))
                logger.warning(f"Rate limited (503). Retry-After: {retry_after}s")
                
                if attempt < retries:
                    time.sleep(retry_after)
                    continue
                else:
                    raise Exception(f"Max retries reached after rate limiting")
            
            # For other errors
            if response.status_code != 200:
                logger.error(f"Request failed with status code: {response.status_code}")
                if attempt < retries:
                    # Calculate delay with exponential backoff and jitter
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                    logger.info(f"Retrying after {delay:.2f}s")
                    time.sleep(delay)
                    continue
                else:
                    response.raise_for_status()
            
            return response
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out (attempt {attempt}/{retries})")
            if attempt < retries:
                # Calculate delay with exponential backoff and jitter
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                logger.info(f"Retrying after {delay:.2f}s")
                time.sleep(delay)
            else:
                raise Exception("All retry attempts timed out")
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e} (attempt {attempt}/{retries})")
            if attempt < retries:
                # Calculate delay with exponential backoff and jitter
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                logger.info(f"Retrying after {delay:.2f}s")
                time.sleep(delay)
            else:
                raise Exception(f"Connection error after {retries} retries: {e}")
                
        except Exception as e:
            logger.error(f"Request failed: {e} (attempt {attempt}/{retries})")
            if attempt < retries:
                # Calculate delay with exponential backoff and jitter
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                logger.info(f"Retrying after {delay:.2f}s")
                time.sleep(delay)
            else:
                raise

def download_pdf_to_cache(identifier: str, pdf_url: str):
    """Download and cache any PDF given a unique identifier"""
    try:
        safe_name = re.sub(r'[^\w\-_.]', '_', identifier)
        file_path = CACHE_DIR / f"{safe_name}.pdf"
        if file_path.exists():
            logger.info(f"PDF already exists: {file_path.name}")
            return

        logger.info(f"Downloading PDF: {pdf_url}")
        resp = requests.get(pdf_url, headers={"User-Agent": USER_AGENT}, timeout=20)
        if resp.status_code == 200 and "application/pdf" in resp.headers.get("Content-Type", ""):
            with open(file_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"Saved PDF: {file_path.name}")
        else:
            logger.warning(f"No PDF found at: {pdf_url}")
    except Exception as e:
        logger.error(f"Error downloading {pdf_url}: {e}")

def search_papers(query: str, max_results: int = DEFAULT_MAX_RESULTS) -> list:
    """
    Search for research papers and download PDFs.

    Args:
        query: Search term
        max_results: Number of papers to return

    Returns:
        List of paper metadata
    """
    try:
        logger.info(f"Searching arXiv for: {query}")
        max_results = min(max_results, 30)  # Cap at 30 to avoid abuse

        search_params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        logger.info(f"Final arXiv search query: {query}")
        response = safe_request(ARXIV_BASE_URL, params=search_params)
        
        # Parse the XML response
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)
        
        # Define XML namespaces
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        entries = root.findall('.//atom:entry', namespaces=ns)
        
        if not entries:
            return [{"message": "No papers found."}]

        papers = []
        for entry in entries:
            # Extract title
            title_elem = entry.find('./atom:title', namespaces=ns)
            title = title_elem.text.strip() if title_elem is not None else "Unknown Title"
            
            # Extract authors
            author_elems = entry.findall('./atom:author/atom:name', namespaces=ns)
            authors = [author.text for author in author_elems]
            
            # Extract publication date
            published_elem = entry.find('./atom:published', namespaces=ns)
            date_str = published_elem.text if published_elem is not None else ""
            year = date_str[:4] if date_str else "N/A"
            
            # Extract abstract
            summary_elem = entry.find('./atom:summary', namespaces=ns)
            abstract = summary_elem.text.strip() if summary_elem is not None else "No abstract available"
            
            # Extract categories
            category_elems = entry.findall('./atom:category', namespaces=ns)
            categories = [cat.get('term') for cat in category_elems]
            category_str = ", ".join(categories) if categories else "N/A"
            
            # Extract links
            pdf_url = ""
            arxiv_id = None
            url = ""
            
            id_elem = entry.find('./atom:id', namespaces=ns)
            if id_elem is not None:
                arxiv_id = id_elem.text.split('/')[-1]
                url = f"https://arxiv.org/abs/{arxiv_id}"
            
            link_elems = entry.findall('./atom:link', namespaces=ns)
            for link in link_elems:
                if link.get('title') == 'pdf':
                    pdf_url = link.get('href')
            
            # Download PDF if available
            if pdf_url and arxiv_id:
                download_pdf_to_cache(arxiv_id, pdf_url)

            # Create paper metadata
            paper = {
                "title": title,
                "authors": authors,
                "year": year,
                "abstract": abstract,
                "categories": category_str,
                "url": url,
                "pdf_url": pdf_url
            }
            
            papers.append(paper)

        return papers

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return [{"error": str(e)}]

def main():
    """Run in standalone mode"""
    parser = argparse.ArgumentParser(description="arXiv Paper Search")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--max_results", type=int, default=DEFAULT_MAX_RESULTS, help="Maximum number of results")
    parser.add_argument("--output", type=str, help="Output file (optional)")
    
    args = parser.parse_args()
    
    papers = search_papers(args.query, args.max_results)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(papers, f, indent=2)
    else:
        print(json.dumps(papers, indent=2))

if __name__ == "__main__":
    # Check if running in MCP mode or standalone mode
    if HAS_MCP and not any(arg.startswith('--') for arg in sys.argv[1:]):
        # MCP mode
        mcp = FastMCP("Paper Search MCP")
        
        @mcp.tool()
        def search_papers_tool(query: str, max_results: int = DEFAULT_MAX_RESULTS) -> list:
            """
            Search for research papers and download PDFs.
            
            Args:
                query: Search term
                max_results: Number of papers to return
            
            Returns:
                List of paper metadata
            """
            return search_papers(query, max_results)
            
        # ADD THIS LINE - This is the key change to keep the server running
        mcp.run()
    else:
        # Standalone mode
        main()