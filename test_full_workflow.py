# test_full_workflow.py
import os
import sys
import asyncio
import json
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Import required modules
from src.data_retrieval.mcp_client import mcp_client  # Note: lowercase class name matches the actual class
from src.query_processing.parser import QueryParser
from src.query_processing.expander import QueryExpander
from src.ranking.ranking_system import RankingSystem
from src.report_generation.generator import ReportGenerator

# Import chunking and metadata components - modified imports to avoid issues
from src.chunking_engine.dynamic_chunker import DynamicChunker
from src.metadata_processing.metadata_extractor import MetadataExtractor
from src.metadata_processing.metadata_validator import MetadataValidator

# Import modified version of EnhancedChunkMetadataConnector to avoid StandardizationService issue
class SimpleMetadataConnector:
    """Simplified connector for enhancing chunks with metadata"""
    
    def __init__(self):
        self.metadata_extractor = MetadataExtractor()
    
    def enhance_mcp_results(self, mcp_results):
        """Enhance MCP results with metadata"""
        if not mcp_results:
            return {"query": "", "chunks": []}
            
        # Extract query and chunks
        query = mcp_results.get("query", "")
        chunks = mcp_results.get("chunks", [])
        
        if not chunks:
            return {"query": query, "chunks": []}
            
        # Get base metadata from the query
        base_metadata = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "source": "mcp_client",
            "source_type": "research_query"
        }
        
        # Process each chunk and enhance with metadata
        enhanced_chunks = []
        
        for chunk in chunks:
            # Create a copy of the chunk
            enhanced_chunk = chunk.copy()
            
            # Extract existing metadata or create empty dict
            chunk_metadata = chunk.get("metadata", {})
            if not chunk_metadata:
                # If no metadata, extract from content
                content_text = chunk.get("text", chunk.get("content", ""))
                chunk_metadata = {
                    "content_length": len(content_text),
                    "source": "research_query",
                    "source_type": "query_result"
                }
            
            # Combine with base metadata
            combined_metadata = {**base_metadata, **chunk_metadata}
            
            # Ensure critical fields exist
            if "title" not in combined_metadata:
                combined_metadata["title"] = "Research Result"
            
            # Update chunk with enhanced metadata
            enhanced_chunk["metadata"] = combined_metadata
            enhanced_chunks.append(enhanced_chunk)
            
        return {
            "query": query,
            "chunks": enhanced_chunks
        }

async def run_workflow(query: str):
    """Run the full Deep Research Engine workflow"""
    print("\n" + "=" * 50)
    print(f"DEEP RESEARCH ENGINE - QUERY: {query}")
    print("=" * 50 + "\n")
    
    # Step 1: Process query
    print("STEP 1: QUERY PROCESSING")
    print("-" * 50)
    
    parser = QueryParser()
    expander = QueryExpander()
    
    # Get cleaned query (just keywords, no explanatory text)
    cleaned_query = parser.clean_query(query)
    
    # DEBUG - Print exactly what's being passed to expander
    print(f"DEBUG - Raw cleaned query being passed to expander: '{cleaned_query}'")
    
    # Pass only the keywords to the expander
    expanded_query = expander.expand_query(cleaned_query)
    
    # DEBUG - Print what came back from expander
    print(f"DEBUG - Raw expanded query from expander: '{expanded_query}'")
    
    # For display purposes, print formatted versions
    print(f"Original Query: {query}")
    print(f"Cleaned Query: {cleaned_query}")
    print(f"Expanded Query: {expanded_query}")
    
    # Step 2: Retrieve data through MCP client - Use the expanded query here!
    print("\nSTEP 2: DATA RETRIEVAL")
    print("-" * 50)
    
    client = mcp_client()  # Create instance with lowercase class name
    
    # IMPORTANT CHANGE: Use the expanded query for the MCP search instead of original query
    print(f"Searching MCP server with query: '{query}'")
    response = await client.process_query(query)  # Use expanded query, not original
    
    chunks = response.get("chunks", [])
    print(f"Retrieved {len(chunks)} content chunks")
    
    if not chunks:
        print("No content chunks retrieved!")
        return
    
    # NEW STEP: Process chunks with metadata
    print("\nNEW STEP: METADATA PROCESSING AND CHUNKING")
    print("-" * 50)
    
    # Use our simplified connector instead of the full version
    metadata_connector = SimpleMetadataConnector()
    
    # Enhance chunks with metadata
    print("Enhancing chunks with metadata...")
    enhanced_results = metadata_connector.enhance_mcp_results({
        "query": query,
        "chunks": chunks
    })
    
    # Extract enhanced chunks
    enhanced_chunks = enhanced_results.get("chunks", [])
    print(f"Enhanced {len(enhanced_chunks)} chunks with metadata")
    
    # Optional: Add content analysis if needed, using try-except to handle potential errors
    try:
        from src.chunking_engine.content_analyzer import ContentAnalyzer
        content_analyzer = ContentAnalyzer()
        content_types = {}
        
        for i, chunk in enumerate(enhanced_chunks[:min(5, len(enhanced_chunks))]):
            try:
                content = chunk.get("content", chunk.get("text", ""))
                if content:
                    doc_type = content_analyzer.analyze(content)
                    content_types[doc_type] = content_types.get(doc_type, 0) + 1
                    # Add content type to metadata
                    if "metadata" in chunk:
                        chunk["metadata"]["content_type"] = doc_type
            except Exception as e:
                print(f"Error analyzing chunk {i}: {str(e)}")
        
        if content_types:
            print(f"Content type distribution (sample): {content_types}")
    except Exception as e:
        print(f"Content analysis not available: {str(e)}")
    
    # Step 3: Rank content (use enhanced chunks now)
    print("\nSTEP 3: CONTENT RANKING")
    print("-" * 50)
    
    ranking_system = RankingSystem()
    
    # Use original query for ranking, as it provides context for relevance scoring
    ranking_result = ranking_system.process_and_rank(query, enhanced_chunks)
    ranked_chunks = ranking_result.get("ranked_chunks", [])
    
    # Display top results
    print(f"\nTop {min(3, len(ranked_chunks))} ranked chunks:")
    for i, chunk in enumerate(ranked_chunks[:3]):
        metadata = chunk.get("metadata", {})
        print(f"\n[{i+1}] {metadata.get('title', 'Untitled')}")
        print(f"   Score: {metadata.get('final_score', 0):.2f}")
        print(f"   Source: {metadata.get('source', 'Unknown')}")
        if "tag" in metadata:
            print(f"   Tag: {metadata.get('tag')}")
        if "content_type" in metadata:
            print(f"   Content Type: {metadata.get('content_type')}")
        if "keywords" in metadata:
            print(f"   Keywords: {', '.join(metadata.get('keywords', []))}")
    
    # Step 4: Generate report
    print("\nSTEP 4: REPORT GENERATION")
    print("-" * 50)
    
    # Create timestamp for output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(project_root, "output", timestamp)
    os.makedirs(output_path, exist_ok=True)
    
    generator = ReportGenerator(output_dir=output_path)
    report_path = generator.generate_report(query, ranked_chunks)
    
    # Save enhanced chunks to JSON
    chunks_path = os.path.join(output_path, "enhanced_chunks.json")
    with open(chunks_path, 'w', encoding='utf-8') as f:
        json.dump({"query": query, "chunks": enhanced_chunks}, f, indent=2)
    print(f"Enhanced chunks saved to: {chunks_path}")
    
    print(f"\nReport generated: {report_path}")
    print(f"All outputs saved to: {output_path}")
    
    # Done
    print("\n" + "=" * 50)
    print("WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 50)

if __name__ == "__main__":
    # Get query from command line or use default
    query = sys.argv[1] if len(sys.argv) > 1 else "quantum computing"
    
    # Run the workflow
    asyncio.run(run_workflow(query))