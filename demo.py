# demo.py
import asyncio
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.query_processing.parser import QueryParser
from src.query_processing.expander import QueryExpander
from src.data_retrieval.orchestrator import DataRetrievalOrchestrator
from src.data_retrieval.content_processor import ContentProcessor

async def run_demo():
    print("===== DEEP RESEARCH ENGINE DEMO =====\n")
    
    # 1. Query processing demo
    print("1. QUERY PROCESSING")
    parser = QueryParser()
    expander = QueryExpander()
    
    # Allow user input or use default query
    default_query = "quantum computing applications in cryptography"
    query = input(f"\nEnter a research query (or press Enter for default '{default_query}'): ")
    
    if not query.strip():
        query = default_query
        print(f"Using default query: {query}")
    
    print("\nProcessing query...")
    cleaned_query = parser.clean_query(query)
    print(f"Cleaned query: {cleaned_query}")
    
    expanded_query = expander.expand_query(cleaned_query)
    print(f"Expanded query: {expanded_query}\n")
    
    # 2. Multi-source search demo
    print("2. MULTI-SOURCE SEARCH")
    orchestrator = DataRetrievalOrchestrator()
    
    print("\nRetrieving data from multiple academic sources...")
    # Use expanded query for better search results
    results = await orchestrator.fetch_all_sources(expanded_query)
    
    print(f"\nFound {len(results)} relevant documents across sources.\n")
    
    # Group results by source
    sources = {}
    for result in results:
        source = result.get('source', 'Unknown')
        if source not in sources:
            sources[source] = []
        sources[source].append(result)
    
    # Display results from each source
    for source_name, source_results in sources.items():
        print(f"\n=== {source_name} Results ({len(source_results)}) ===")
        
        # Display up to 3 results from each source
        for i, result in enumerate(source_results[:3], 1):
            # Truncate title if too long
            title = result.get('title', 'No title')[:80] + ('...' if len(result.get('title', '')) > 80 else '')
            
            print(f"Result {i}: {title}")
            print(f"URL: {result.get('url', 'No URL')}")
            
            # Get summary or snippet, whichever is available
            summary = result.get('summary', result.get('snippet', 'No summary available'))
            print(f"Summary: {summary[:150]}...\n" if len(summary) > 150 else f"Summary: {summary}\n")
    
    # 3. Content processing demo
    if results:
        processor = ContentProcessor()
        print("3. CONTENT PROCESSING")
        print("\nProcessing a sample document...")
        
        # Get the first result with good content
        sample = next((r for r in results if r.get('summary', r.get('snippet', ''))), results[0])
        content = sample.get('summary', sample.get('snippet', ''))
        
        if content:
            processed = processor.process_content(content, url=sample.get('url', ''))
            
            print(f"\nOriginal size: {len(content)} characters")
            print(f"Processed size: {len(processed['text'])} characters")
            print(f"Content type: {processed['metadata']['content_type']}/{processed['metadata']['subtype']}")
            print(f"Sample from: {sample.get('title', 'Unknown document')} ({sample.get('source', 'Unknown source')})")
            print(f"Extracted content sample:\n---\n{processed['text'][:300]}...\n---")
        else:
            print("\nNo content available for processing in the sample document.")
    else:
        print("\nNo results found to process.")
    
    print("\n===== DEMO COMPLETED =====")

if __name__ == "__main__":
    asyncio.run(run_demo())