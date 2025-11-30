# tests/test_mcp_client.py
import sys
import os
import asyncio
import json

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.data_retrieval.mcp_client import MCPClient

async def test_mcp_client():
    """Test the MCP client with a running server"""
    client = MCPClient()
    print("Testing MCP client...")
    
    try:
        # Try to query the running server
        result = await client.process_query("quantum computing")
        print(f"Success! Got {len(result.get('chunks', []))} chunks")
        
        # Print first chunk text snippet
        if result.get('chunks'):
            print(f"Sample text: {result['chunks'][0]['text'][:100]}...")
        return True
    except Exception as e:
        print(f"Error: {e}")
        print("Note: This can happen if the server is not running or if there are API rate limit issues")
        return False

if __name__ == "__main__":
    asyncio.run(test_mcp_client())