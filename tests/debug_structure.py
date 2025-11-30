# debug_structure.py
import os
import sys

def print_directory_structure(start_path):
    """Print the directory structure starting from start_path"""
    print(f"Project structure from: {start_path}")
    print("-" * 50)
    
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")

def check_imports():
    """Try to import key modules and report results"""
    print("\nTesting key imports:")
    print("-" * 50)
    
    # Define modules to test
    modules = [
        "src",
        "src.data_retrieval",
        "src.data_retrieval.mcp_client",
        "src.query_processing",
        "src.ranking"
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ Successfully imported: {module}")
        except ImportError as e:
            print(f"❌ Failed to import: {module}")
            print(f"   Error: {str(e)}")

def check_environment():
    """Print information about the Python environment"""
    print("\nEnvironment information:")
    print("-" * 50)
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.executable}")
    print("\nPython path entries:")
    for path in sys.path:
        print(f"  {path}")

if __name__ == "__main__":
    # Current directory
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Print basic info
    print("\n" + "=" * 60)
    print("DEBUG INFORMATION FOR DEEP RESEARCH ENGINE")
    print("=" * 60 + "\n")
    
    # Print directory structure (only 2 levels deep for clarity)
    print_directory_structure(current_dir)
    
    # Check imports
    check_imports()
    
    # Check environment
    check_environment()