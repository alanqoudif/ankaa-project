"""Environment variable loader for ShariaAI application."""
import os
from dotenv import load_dotenv

def load_env_vars():
    """Load environment variables from .env file."""
    # Load .env file if it exists
    load_dotenv()
    
    # Get API keys
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    llamaindex_api_key = os.getenv("LLAMAINDEX_API_KEY")
    legal_files_dir = os.getenv("LEGAL_FILES_DIR")
    
    # Use default values if environment variables are not set
    if not openrouter_api_key:
        openrouter_api_key = "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"
        print("Warning: OPENROUTER_API_KEY not found in environment variables. Using default key.")
    
    if not llamaindex_api_key:
        llamaindex_api_key = "llx-gtcRZJSsolYe3nOrX80tXf5cMySyp2K4KdCd14HbWcTor3jz"
        print("Warning: LLAMAINDEX_API_KEY not found in environment variables. Using default key.")
    
    if not legal_files_dir:
        legal_files_dir = "/Users/faisalalanqoudi/anka-project/data"
        print("Warning: LEGAL_FILES_DIR not found in environment variables. Using default directory.")
    
    return {
        "openrouter_api_key": openrouter_api_key,
        "llamaindex_api_key": llamaindex_api_key,
        "legal_files_dir": legal_files_dir
    }
