# test_mcp_standalone.py

import os
import sys
import asyncio
import json
import subprocess

# Get the absolute path to the project root directory
project_root = os.path.abspath(os.path.dirname(__file__))

# Add project root to Python path
sys.path.insert(0, project_root)

print(f"Project root: {project_root}")
print(f"Files in project root: {os.listdir(project_root)}")

# Check if src directory exists
if "src" in os.listdir(project_root):
    print(f"✅ src directory found")
    # Check if it has the expected structure
    src_path = os.path.join(project_root, "src")
    print(f"Files in src directory: {os.listdir(src_path)}")
else:
    print(f"❌ src directory not found in project root!")
    # See if it's one level up
    parent_dir = os.path.dirname(project_root)
    if "src" in os.listdir(parent_dir):
        print(f"Found src directory in parent directory: {parent_dir}")
        # Add parent directory to path
        sys.path.insert(0, parent_dir)
        project_root = parent_dir

# Try to run a direct test with the MCP server
async def test_mcp_server():
    """Test the MCP server directly with a subprocess call"""
    print("\nTesting MCP server with direct subprocess call...")
    
    try:
        # Run the server with a test query
        process = await asyncio.create_subprocess_exec(
            "python", os.path.join(project_root, "mcp-service", "server.py"),
            "--query", "quantum computing",
            "--max_results", "2",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Parse the response
            response = stdout.decode('utf-8')
            try:
                data = json.loads(response)
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ Server returned {len(data)} papers")
                    print(f"Sample paper title: {data[0].get('title', 'N/A')}")
                    return True
                else:
                    print(f"❌ Server returned empty or invalid data: {data}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ Server response is not valid JSON")
                print(f"Response: {response[:200]}...")
                return False
        else:
            print(f"❌ Server command failed with code {process.returncode}")
            if stderr:
                print(f"Error: {stderr.decode('utf-8')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_mcp_server())
    
    # Try to import the mcp_client module directly
    try:
        # For testing, add all potential paths
        for path in [project_root, os.path.dirname(project_root)]:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        print("\nTrying to manually import mcp_client...")
        # Try various import paths
        try:
            from src.data_retrieval.mcp_client import MCPClient
            print("✅ Successfully imported MCPClient")
        except ImportError as e1:
            print(f"❌ Failed to import from src.data_retrieval.mcp_client: {e1}")
            try:
                from src.data_retrieval.mcp_client import MCPClient
                print("✅ Successfully imported MCPClient (without src prefix)")
            except ImportError as e2:
                print(f"❌ Failed to import from data_retrieval.mcp_client: {e2}")
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")