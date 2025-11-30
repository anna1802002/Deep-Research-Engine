# scripts/setup_api_keys.py

import os
import yaml
import getpass
import sys

def setup_api_keys():
    """Interactive script to set up API keys for Deep Research Engine."""
    print("\n🔑 Deep Research Engine - API Keys Setup 🔑\n")
    
    # Ensure config directory exists
    config_dir = "config"
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"✅ Created config directory at {config_dir}")
    
    # Define the path for the API keys file
    api_keys_path = os.path.join(config_dir, "api_keys.yaml")
    
    # Check if file already exists
    existing_keys = {}
    if os.path.exists(api_keys_path):
        try:
            with open(api_keys_path, 'r') as f:
                existing_keys = yaml.safe_load(f) or {}
            print(f"📝 Found existing API keys configuration")
        except Exception as e:
            print(f"⚠️ Error reading existing config: {e}")
    
    # API keys needed for the project
    required_keys = {
        "GOOGLE_API_KEY": "Google Custom Search API Key",
        "GOOGLE_CSE_ID": "Google Custom Search Engine ID",
        "GOOGLE_SCHOLAR_API_KEY": "Google Scholar API Key (can be same as Custom Search)",
        "GOOGLE_SCHOLAR_CX": "Google Scholar Custom Search Engine ID",
        "OPENAI_API_KEY": "OpenAI API Key (for embeddings)",
        "GROQ_API_KEY": "GROQ API Key (for query expansion)"
    }
    
    # Update keys
    for key_name, description in required_keys.items():
        current_value = existing_keys.get(key_name, "")
        
        if current_value:
            print(f"\n{description}")
            change = input(f"Current {key_name} exists. Change it? (y/n, default: n): ").lower() == 'y'
            
            if change:
                new_value = getpass.getpass(f"Enter new {key_name}: ")
                existing_keys[key_name] = new_value
                print(f"✅ Updated {key_name}")
        else:
            print(f"\n{description}")
            new_value = getpass.getpass(f"Enter {key_name}: ")
            
            if new_value:
                existing_keys[key_name] = new_value
                print(f"✅ Added {key_name}")
            else:
                print(f"⚠️ No value provided for {key_name}")
    
    # Save the updated configuration
    try:
        with open(api_keys_path, 'w') as f:
            yaml.dump(existing_keys, f, default_flow_style=False)
        
        # Set secure permissions
        os.chmod(api_keys_path, 0o600) # Only owner can read/write
        
        print(f"\n✅ API keys saved to {api_keys_path}")
        print("⚠️ Keep this file secure and do not commit it to version control!")
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False
        
    return True

def verify_api_keys():
    """Verify API keys are properly configured."""
    api_keys_path = os.path.join("config", "api_keys.yaml")
    
    if not os.path.exists(api_keys_path):
        print(f"❌ API keys file not found at {api_keys_path}")
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
            print(f"❌ Missing API keys: {', '.join(missing_keys)}")
            return False
            
        print("✅ All required API keys are configured")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying API keys: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        success = verify_api_keys()
    else:
        success = setup_api_keys()
        
    sys.exit(0 if success else 1)