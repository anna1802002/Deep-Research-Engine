# src/data_retrieval/mcp_client.py - Revised with workflow integration focus
from typing import Dict, List, Any
import asyncio
import logging
import os
from pathlib import Path
import json
import time
import random
import requests
import yaml
from src.chunking.chunker_factory import ChunkerFactory

logger = logging.getLogger("deep_research.data_retrieval.mcp_client")

class mcp_client:
    def __init__(self):
        """Initialize MCP client"""
        logger.info("Initializing MCP client")
        
        # Path to paper cache directory (inside mcp-service folder)
        self.paper_cache_dir = Path("mcp-service/paper_cache")
        if not self.paper_cache_dir.exists():
            self.paper_cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created paper cache directory: {self.paper_cache_dir}")
        
        # Create chunker instance
        self.chunker = ChunkerFactory.create_chunker()
        
        # Load settings
        self.settings = self._load_settings()
        self.mcp_endpoint = self.settings.get("mcp", {}).get("endpoint", "http://localhost:8001/mcp")
        self.timeout = self.settings.get("mcp", {}).get("timeout", 30)
        
        # Rate limiting settings
        self.max_retries = 5
        self.initial_delay = 3  # seconds
        
        logger.info(f"MCP client initialized with endpoint: {self.mcp_endpoint}")
    
    def _load_settings(self):
        """Load settings from settings.yaml"""
        settings_path = "config/settings.yaml"
        try:
            with open(settings_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return {}
    
    async def process_query(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Process query through MCP server and integrate with the existing pipeline.
        
        This method:
        1. Uses the MCP server to search for papers using the provided query
        2. Processes the papers through our existing chunking system
        3. Returns chunks in the format expected by our ranking system
        
        Note: The query should already be processed by the external query processing 
        pipeline before being passed to this method.
        
        Args:
            query: The processed query to send to the MCP server
            max_results: Maximum number of results to return
                
        Returns:
            Dictionary with query and content chunks
        """
        try:
            logger.info(f"Sending query to MCP server: {query}")
            
            # Run the server process with retries
            papers_response = await self._execute_mcp_search(query, max_results)
            
            if not papers_response:
                logger.warning("No response from server process")
                return {"query": query, "chunks": []}
            
            # Parse the response (assuming JSON format)
            papers = []
            try:
                papers = json.loads(papers_response)
                if not isinstance(papers, list):
                    papers = [papers]
                logger.info(f"Parsed {len(papers)} papers from response")
            except json.JSONDecodeError:
                # If not JSON, try to parse it as a formatted string
                logger.warning("Response is not valid JSON, attempting to parse as text")
                papers = self._parse_text_response(papers_response)
            
            # Transform papers to our internal format
            chunks = []
            
            # Process each paper into a chunk
            for paper in papers:
                # Skip error entries
                if isinstance(paper, dict) and "error" in paper:
                    logger.error(f"Error in paper result: {paper['error']}")
                    continue
                
                # Skip "no papers found" messages
                if isinstance(paper, dict) and "message" in paper and "No papers found" in paper["message"]:
                    logger.warning(f"No papers found for query: {query}")
                    return {"query": query, "chunks": []}
                
                # Create content for chunking from the abstract
                abstract = paper.get("abstract", "")
                # Skip empty abstracts
                if not abstract or len(abstract.strip()) < 10:
                    logger.warning(f"Skipping paper with empty/short abstract: {paper.get('title', 'Unknown')}")
                    continue
                    
                abstract_content = {
                    "text": abstract,
                    "metadata": {
                        "source": "arXiv",
                        "url": paper.get("url", ""),
                        "title": paper.get("title", ""),
                        "publication_date": str(paper.get("year", "")),
                        "source_type": "academic",
                        "authors": paper.get("authors", []),
                        "categories": paper.get("categories", ""),
                        "pdf_url": paper.get("pdf_url", "")
                    }
                }
                
                # Run the abstract through our chunker to maintain consistency
                abstract_chunks = self.chunker.create_chunks(abstract_content)
                chunks.extend(abstract_chunks)
                
                # Now process any PDFs that were downloaded
                arxiv_id = None
                if paper.get("url"):
                    # Extract arXiv ID from URL
                    import re
                    id_match = re.search(r'abs/([^/]+)$', paper.get("url", ""))
                    if id_match:
                        arxiv_id = id_match.group(1)
                        
                if arxiv_id:
                    # Check if PDF exists before trying to process it
                    import re
                    safe_id = re.sub(r'[^\w\-_.]', '_', arxiv_id)
                    pdf_path = self.paper_cache_dir / f"{safe_id}.pdf"
                    
                    if pdf_path.exists():
                        logger.info(f"Processing PDF for arxiv ID: {arxiv_id}")
                        pdf_chunks = self._process_pdf(arxiv_id, paper)
                        if pdf_chunks:
                            chunks.extend(pdf_chunks)
                    else:
                        logger.info(f"PDF not found for arxiv ID: {arxiv_id} (this is normal if paper wasn't downloaded)")
            
            # If no chunks were created, return a helpful message
            if not chunks:
                logger.warning(f"No valid chunks created from query: {query}")
                return {
                    "query": query,
                    "chunks": [{
                        "text": f"Unable to find relevant academic papers for '{query}'. Try a different query or check that arXiv API is accessible.",
                        "metadata": {
                            "source": "Fallback",
                            "title": f"No results for: {query}",
                            "source_type": "fallback"
                        }
                    }]
                }
                
            logger.info(f"Processed query through MCP, received {len(chunks)} chunks")
            return {"query": query, "chunks": chunks}
        
        except Exception as e:
            logger.error(f"Error communicating with MCP server: {e}")
            # Return fallback data when API fails
            return {
                "query": query,
                "chunks": [{
                    "text": f"Unable to retrieve data for '{query}' due to an error: {str(e)}. This is a fallback response.",
                    "metadata": {
                        "source": "Fallback",
                        "title": f"Fallback content for: {query}",
                        "source_type": "fallback"
                    }
                }]
            }
    
    async def _execute_mcp_search(self, query: str, max_results: int) -> str:
        """
        Execute MCP search with retry logic.
        
        Args:
            query: The search query
            max_results: Maximum number of results
            
        Returns:
            Response string from the MCP server
        """
        for retry in range(self.max_retries):
            try:
                # Run the server process directly and get output
                process = await asyncio.create_subprocess_exec(
                    "python", 
                    "mcp-service/server.py",
                    "--query", query,  # This should already be the processed query from your pipeline
                    "--max_results", str(max_results),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Wait for process and get output with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout
                )
                
                if process.returncode != 0:
                    stderr_text = stderr.decode('utf-8')
                    logger.warning(f"Server process failed with code {process.returncode}: {stderr_text}")
                    
                    # Check if this is a rate limit error
                    if "429" in stderr_text or "503" in stderr_text or "Connection reset" in stderr_text:
                        # Calculate wait time with exponential backoff and jitter
                        wait_time = self.initial_delay * (2 ** retry) + random.uniform(0, 1)
                        logger.info(f"Rate limit encountered, retrying after {wait_time:.2f} seconds (attempt {retry+1}/{self.max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        return ""
                
                papers_response = stdout.decode('utf-8')
                return papers_response
                
            except asyncio.TimeoutError:
                logger.warning(f"Server process timed out after {self.timeout} seconds (attempt {retry+1}/{self.max_retries})")
                if retry < self.max_retries - 1:
                    # Calculate wait time with exponential backoff and jitter
                    wait_time = self.initial_delay * (2 ** retry) + random.uniform(0, 1)
                    logger.info(f"Retrying after {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("All retry attempts failed due to timeouts")
                    return ""
        
        # We only get here if all retries failed
        logger.error("All retry attempts failed")
        return ""
    
    def _parse_text_response(self, text_response: str) -> List[Dict]:
        """Parse a text response into a list of paper dictionaries"""
        logger.info("Parsing text response from MCP server")
        
        # Simple parsing for demonstration - adjust based on actual format
        papers = []
        
        # If there's a clear paper separator in the text
        paper_sections = text_response.split("---")
        
        for section in paper_sections:
            if not section.strip():
                continue
                
            paper = {}
            lines = section.strip().split("\n")
            
            current_field = None
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == "title":
                        paper["title"] = value
                    elif key == "authors":
                        paper["authors"] = [a.strip() for a in value.split(",")]
                    elif key == "year":
                        paper["year"] = value
                    elif key == "abstract":
                        paper["abstract"] = value
                    elif key == "url" or key == "link":
                        paper["url"] = value
                    current_field = key
                elif current_field:
                    # Continuation of previous field
                    paper[current_field] = paper.get(current_field, "") + " " + line.strip()
            
            if paper:
                papers.append(paper)
                
        logger.info(f"Parsed {len(papers)} papers from text response")
        return papers
    
    def _process_pdf(self, arxiv_id: str, paper_metadata: Dict) -> List[Dict]:
        """
        Process a downloaded PDF using our existing chunking system.
        
        Args:
            arxiv_id: The arXiv ID to locate the PDF
            paper_metadata: Metadata about the paper
            
        Returns:
            List of chunks from the PDF
        """
        try:
            # Sanitize arxiv_id for filename
            import re
            safe_id = re.sub(r'[^\w\-_.]', '_', arxiv_id)
            pdf_path = self.paper_cache_dir / f"{safe_id}.pdf"
            
            if not pdf_path.exists():
                logger.warning(f"PDF not found at {pdf_path}")
                return []
            
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Use your existing PDF extraction module
            from src.data_retrieval.content_processor import ContentProcessor
            processor = ContentProcessor()
            
            # Read PDF and extract text
            with open(pdf_path, "rb") as f:
                pdf_content = f.read()
            
            # Process the PDF content
            processed_content = processor.process_content(
                pdf_content, 
                url=paper_metadata.get("url", ""),
                source_type="academic"
            )
            
            if not processed_content or not processed_content.get("text"):
                logger.warning(f"Failed to extract text from PDF: {pdf_path}")
                return []
            
            # Add more detailed metadata
            processed_content["metadata"].update({
                "title": paper_metadata.get("title", ""),
                "authors": paper_metadata.get("authors", []),
                "publication_date": str(paper_metadata.get("year", "")),
                "categories": paper_metadata.get("categories", ""),
                "source": "arXiv",
                "source_type": "academic",
                "content_type": "pdf"
            })
            
            # Use the chunker to create chunks
            pdf_chunks = self.chunker.create_chunks(processed_content)
            logger.info(f"Created {len(pdf_chunks)} chunks from PDF")
            
            return pdf_chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return []
            
    async def test_connection(self) -> bool:
        """Test the connection to the MCP server with retry logic"""
        try:
            # Simple test query to check if server.py can be executed
            for retry in range(3):
                try:
                    process = await asyncio.create_subprocess_exec(
                        "python", 
                        "mcp-service/server.py",
                        "--query", "test",
                        "--max_results", "1",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    # Wait for process with timeout
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
                    
                    if process.returncode == 0 and stdout:
                        return True
                    else:
                        stderr_text = stderr.decode('utf-8')
                        logger.warning(f"Server test failed (attempt {retry+1}/3): {stderr_text}")
                        await asyncio.sleep(2 ** retry)  # Exponential backoff
                        
                except asyncio.TimeoutError:
                    logger.warning(f"Server test timed out (attempt {retry+1}/3)")
                    await asyncio.sleep(2 ** retry)  # Exponential backoff
                    
            return False
            
        except Exception as e:
            logger.error(f"MCP connection test failed: {e}")
            return False