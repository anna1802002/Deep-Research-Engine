#!/usr/bin/env python3
"""
Deep Research Engine - Complete Demo

This script demonstrates the full pipeline of the Deep Research Engine:
1. Query Processing
2. Multi-Source Data Retrieval
3. Content Processing
4. Ranking
5. Report Generation

It uses local embeddings to avoid API dependency issues.
"""

import sys
import os
import asyncio
import time
import logging
from datetime import datetime
import argparse
from typing import List, Dict
import json

# Try to import markdown, fall back gracefully if not available
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("Warning: markdown module not found. HTML reports will not be generated.")

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.append(project_root)

# Import components
try:
    from src.query_processing.parser import QueryParser
    from src.query_processing.expander import QueryExpander
    from src.data_retrieval.orchestrator import DataRetrievalOrchestrator
    from src.ranking.ranking_system import RankingSystem
    from src.chunking.chunker_factory import ChunkerFactory
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Make sure you're running the script from the project root directory.")
    sys.exit(1)

# Configure logging
log_dir = os.path.join(project_root, "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, "demo.log"))
    ]
)
logger = logging.getLogger("demo")

def print_section(title):
    """Print a section header."""
    width = 80
    print("\n" + "=" * width)
    padding = (width - len(title)) // 2
    print(" " * padding + title)
    print("=" * width + "\n")

def list_to_summary(items, max_items=3):
    """Convert a list of items to a summary string."""
    if not items:
        return "None"
    
    if len(items) > max_items:
        return f"{', '.join(items[:max_items])} and {len(items) - max_items} more"
    return ', '.join(items)

async def fetch_multi_source_data(query: str) -> List[Dict]:
    """Fetch data from all integrated sources."""
    print_section("DATA RETRIEVAL")
    print(f"Retrieving data for query: '{query}'")
    
    start_time = time.time()
    
    # Initialize data retrieval orchestrator
    orchestrator = DataRetrievalOrchestrator()
    
    # Fetch data from all sources
    results = await orchestrator.fetch_all_sources(query)
    
    duration = time.time() - start_time
    print(f"Retrieved {len(results)} documents in {duration:.2f} seconds\n")
    
    # Summarize results by source
    sources = {}
    for result in results:
        source = result.get('source', 'Unknown')
        if source not in sources:
            sources[source] = 0
        sources[source] += 1
    
    print("Documents by source:")
    for source, count in sources.items():
        print(f"  - {source}: {count} documents")
    
    return results

def process_and_rank(query: str, results: List[Dict], top_n: int = 10) -> Dict:
    """Process, chunk, and rank the retrieved content."""
    print_section("CONTENT PROCESSING & RANKING")
    print(f"Processing and ranking {len(results)} documents...")
    
    start_time = time.time()
    
    # Initialize chunker
    chunker = ChunkerFactory.create_chunker()
    
    # Initialize ranking system
    ranking_system = RankingSystem()
    
    # Process each result into chunks
    all_chunks = []
    for result in results:
        # Create content dict expected by chunker
        content = {
            "text": result.get('summary', result.get('snippet', '')),
            "metadata": {
                "url": result.get('url', ''),
                "title": result.get('title', 'Untitled'),
                "source_type": 'academic' if result.get('source') in ['ArXiv', 'PubMed', 'Google Scholar'] else 'web',
                "publication_date": datetime.now().strftime("%Y-%m-%d")  # Default to today
            }
        }
        
        # Skip empty content
        if not content["text"].strip():
            continue
            
        # Create chunks
        chunks = chunker.create_chunks(content)
        all_chunks.extend(chunks)
    
    # Rank the chunks
    ranking_result = ranking_system.process_and_rank(query, all_chunks, top_n=top_n)
    
    duration = time.time() - start_time
    print(f"Processed and ranked content in {duration:.2f} seconds")
    print(f"Selected top {len(ranking_result['ranked_chunks'])} chunks from {len(all_chunks)} total chunks")
    
    return ranking_result

def generate_report(query: str, ranking_result: Dict, output_path: str) -> str:
    """Generate a markdown report from the ranked chunks."""
    print_section("REPORT GENERATION")
    print(f"Generating research report for query: '{query}'")
    
    ranked_chunks = ranking_result.get('ranked_chunks', [])
    if not ranked_chunks:
        print("No relevant content found to generate report")
        return ""
    
    # Create report directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Build report content
    report = [
        f"# Research Report: {query}",
        f"\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        
        "\n## Summary",
        f"This report contains the top {len(ranked_chunks)} most relevant excerpts from various sources related to your query.",
        
        "\n## Key Findings"
    ]
    
    # Add each chunk as a section
    for i, chunk in enumerate(ranked_chunks):
        # Extract metadata
        metadata = chunk.get('metadata', {})
        source = metadata.get('title', 'Unknown Source')
        url = metadata.get('url', '#')
        score = metadata.get('final_score', 0)
        source_type = metadata.get('source_type', 'web')
        
        # Add section
        report.append(f"\n### {i+1}. {source}")
        report.append(f"**Source Type**: {source_type.title()}")
        report.append(f"**Relevance Score**: {score:.2f}")
        report.append(f"**URL**: {url}")
        report.append("")
        report.append(chunk.get('text', ''))
    
    # Add bibliography
    report.append("\n## Sources")
    sources = set()
    for chunk in ranked_chunks:
        url = chunk.get('metadata', {}).get('url')
        title = chunk.get('metadata', {}).get('title', 'Unknown')
        if url and url not in sources:
            sources.add(url)
            report.append(f"- [{title}]({url})")
    
    # Write report to file
    report_content = "\n".join(report)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"Markdown report generated: {output_path}")
    
    # Only generate HTML if markdown is available
    if MARKDOWN_AVAILABLE:
        html_path = output_path.replace('.md', '.html')
        html_content = markdown.markdown(report_content)
        
        # Create a simple HTML page
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Report: {query}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #3498db; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        h3 {{ color: #2980b9; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .metadata {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 15px; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>""")
        
        print(f"HTML report generated: {html_path}")
    
    return output_path

async def process_query(query_text: str) -> Dict:
    """Process the query text to expand and clean it."""
    print_section("QUERY PROCESSING")
    print(f"Processing query: '{query_text}'")
    
    # Initialize query processors
    parser = QueryParser()
    expander = QueryExpander()
    
    # Process the query
    try:
        cleaned_query = parser.clean_query(query_text)
        print(f"Cleaned query: {cleaned_query}")
        
        expanded_query = expander.expand_query(cleaned_query)
        print(f"Expanded query: {expanded_query}")
        
        return {
            "original": query_text,
            "cleaned": cleaned_query,
            "expanded": expanded_query
        }
    except Exception as e:
        print(f"Error processing query: {e}")
        # Fall back to original query
        return {
            "original": query_text,
            "cleaned": query_text,
            "expanded": query_text
        }

async def run_demo(query_text: str, top_n: int = 10):
    """Run the complete Deep Research Engine pipeline."""
    print_section("DEEP RESEARCH ENGINE DEMO")
    print(f"Starting research on: '{query_text}'")
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory
    output_dir = os.path.join(project_root, "output", timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Process query
    query_info = await process_query(query_text)
    
    # 2. Fetch data from multiple sources
    results = await fetch_multi_source_data(query_info['expanded'])
    
    # Save raw results
    with open(os.path.join(output_dir, "raw_results.json"), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 3. Process and rank content
    ranking_result = process_and_rank(query_text, results, top_n)
    
    # 4. Generate report
    report_path = os.path.join(output_dir, "research_report.md")
    generate_report(query_text, ranking_result, report_path)
    
    print_section("DEMO COMPLETED")
    print(f"All outputs saved to: {output_dir}")
    return output_dir

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Deep Research Engine Demo")
    parser.add_argument("query", nargs="?", default="quantum computing applications in cryptography",
                        help="Research query (default: 'quantum computing applications in cryptography')")
    parser.add_argument("--top", type=int, default=10, help="Number of top results to include (default: 10)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    try:
        output_dir = asyncio.run(run_demo(args.query, args.top))
    except Exception as e:
        print(f"Error running demo: {e}")
        sys.exit(1)