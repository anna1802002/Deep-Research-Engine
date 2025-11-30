#!/usr/bin/env python3
"""
Deep Research Engine - End-to-End Demo (Revised)

This script demonstrates the complete workflow with improved output formatting:
1. Query processing
2. Data retrieval via MCP (mocked)
3. Content ranking
4. Report generation
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime
import json
from typing import Dict, List, Any

import socket
import time

# Add this function to run_demo.py
import socket
import time
import subprocess

def is_mcp_server_running(port=8000, test_query=True):
    """Check if MCP server is running and responsive"""
    # First check if something is running on the port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        port_active = s.connect_ex(('localhost', port)) == 0
    
    # If port check fails, return False
    if not port_active:
        return False
    
    # If port is active and test_query is True, also test with a query
    if test_query:
        try:
            # Run the server with a test query
            result = subprocess.run(
                ["python", "mcp-service/server.py", "--query", "test", "--max_results", "1"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    return True

def is_port_in_use(port=8000):
    """Always return True for testing"""
    # Instead of checking the port, check if server.py can be executed
    try:
        result = subprocess.run(
            ["python", "mcp-service/server.py", "--query", "test", "--max_results", "1"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        # If subprocess fails, check the port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        except:
            return False

# Check if MCP server is running
if not is_port_in_use(8000):
    print("⚠️ MCP server is not running!")
    print("Please start the MCP server in a separate terminal with:")
    print("   ./scripts/start_mcp_server.sh")
    print("Then run this script again.")
    sys.exit(1)

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("demo.log")
    ]
)
logger = logging.getLogger("demo")

def print_section(title: str, width: int = 80) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * width}")
    print(f"{title.center(width)}")
    print(f"{'=' * width}\n")

async def run_demo(query: str, output_dir: str = "output") -> Dict[str, Any]:
    """
    Run the complete research workflow with improved output handling.
    
    Args:
        query: Research query
        output_dir: Directory for output files
    
    Returns:
        Dictionary containing results and paths
    """
    print_section(f"DEEP RESEARCH ENGINE DEMO - {query}")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, timestamp)
    os.makedirs(output_path, exist_ok=True)
    
    # Step 1: Process query
    print_section("STEP 1: QUERY PROCESSING")
    from src.query_processing.parser import QueryParser
    from src.query_processing.expander import QueryExpander
    from src.query_processing.vectorizer import QueryVectorizer
    
    parser = QueryParser()
    expander = QueryExpander()
    vectorizer = QueryVectorizer()
    
    # Process the query
    cleaned_query = parser.clean_query(query)
    expanded_query = expander.expand_query(cleaned_query)
    query_embedding = vectorizer.vectorize_query(expanded_query)
    
    print(f"Original Query: {query}")
    print(f"Cleaned Query: {cleaned_query}")
    print(f"Expanded Query: {expanded_query}")
    
    # Step 2: Retrieve data via MCP
    print_section("STEP 2: DATA RETRIEVAL")
    from src.data_retrieval.mcp_client import MCPClient
    
    mcp_client = MCPClient()
    mcp_response = await mcp_client.process_query(expanded_query)
    
    chunks = mcp_response.get("chunks", [])
    print(f"\nRetrieved {len(chunks)} content chunks")
    
    # Save raw data
    with open(os.path.join(output_path, "raw_results.json"), "w", encoding="utf-8") as f:
        json.dump(mcp_response, f, indent=2, default=str)
    
    if not chunks:
        print("Warning: No content chunks retrieved!")
        return {
            "query": query,
            "output_path": output_path,
            "report_path": None,
            "ranked_chunks": 0
        }
    
    # Step 3: Rank content
    print_section("STEP 3: CONTENT RANKING")
    from src.ranking.ranking_system import RankingSystem
    
    ranking_system = RankingSystem()
    
    query_obj = {
        "text": expanded_query,
        "metadata": {
            "embedding": query_embedding
        }
    }
    
    ranking_result = ranking_system.process_and_rank(query_obj, chunks)
    ranked_chunks = ranking_result.get("ranked_chunks", [])
    
    # Display top results
    print(f"\nTop {min(3, len(ranked_chunks))} ranked chunks:")
    for i, chunk in enumerate(ranked_chunks[:3]):
        metadata = chunk.get("metadata", {})
        print(f"\n[{i+1}] {metadata.get('title', 'Untitled')}")
        print(f"   Score: {metadata.get('final_score', 0):.2f}")
        print(f"   Source: {metadata.get('source', 'Unknown')}")
        print(f"   Date: {metadata.get('date', 'N/A')}")
        print(f"   Keywords: {', '.join(metadata.get('keywords', []))}")
    
    # Step 4: Generate report
    print_section("STEP 4: REPORT GENERATION")
    from src.report_generation.generator import ReportGenerator
    
    generator = ReportGenerator(output_dir=output_path)
    report_path = generator.generate_report(query, ranked_chunks)
    
    print(f"\nReport generated: {report_path}")
    print(f"All outputs saved to: {output_path}")
    
    return {
        "query": query,
        "output_path": output_path,
        "report_path": report_path,
        "ranked_chunks": len(ranked_chunks)
    }

def main() -> None:
    """Main function to handle query input and run the demo."""
    parser = argparse.ArgumentParser(description="Run Deep Research Engine Demo")
    parser.add_argument("query", nargs="?", 
                       help="Research query to process")
    parser.add_argument("--output", "-o", default="output",
                       help="Output directory (default: output)")
    
    args = parser.parse_args()
    
    # If no query provided via argument, prompt interactively
    if not args.query:
        print_section("DEEP RESEARCH ENGINE - QUERY INPUT")
        query = input("\nEnter your research query: ").strip()
        
        # Validate query input
        while not query:
            print("Error: Query cannot be empty.")
            query = input("Enter your research query: ").strip()
    else:
        query = args.query
    
    # Run the demo
    try:
        result = asyncio.run(run_demo(query, args.output))
        
        print_section("DEMO COMPLETED")
        if result["report_path"]:
            print(f"\nResearch report generated at: {result['report_path']}")
        else:
            print("\nNo report generated - no content chunks were ranked")
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()