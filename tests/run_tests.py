# tests/run_tests.py

import unittest
import sys
import os
import yaml

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def check_api_keys():
    """Verify API keys before running tests."""
    api_keys_path = os.path.join("config", "api_keys.yaml")
    
    if not os.path.exists(api_keys_path):
        print(f"⚠️ API keys file not found at {api_keys_path}")
        print("ℹ️ Run `python scripts/setup_api_keys.py` to configure your API keys")
        return False
        
    try:
        with open(api_keys_path, 'r') as f:
            keys = yaml.safe_load(f) or {}
            
        required_keys = [
            "GOOGLE_API_KEY", 
            "GOOGLE_CSE_ID", 
            "GOOGLE_SCHOLAR_API_KEY", 
            "GOOGLE_SCHOLAR_CX",
            "OPENAI_API_KEY",
            "GROQ_API_KEY"
        ]
        
        missing_keys = [k for k in required_keys if not keys.get(k)]
        
        if missing_keys:
            print(f"⚠️ Missing API keys: {', '.join(missing_keys)}")
            print("ℹ️ Some tests may be skipped due to missing API keys")
            return False
            
        print("✅ All required API keys are configured")
        return True
        
    except Exception as e:
        print(f"⚠️ Error checking API keys: {e}")
        return False

def run_tests():
    """Run all tests for the Deep Research Engine."""
    # Check API keys first
    check_api_keys()
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())