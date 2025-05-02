"""Environment variable loader for ShariaAI application."""
import os
import logging
import requests
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
        # Try the demo key first
        openrouter_api_key = "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"
        logging.warning("OPENROUTER_API_KEY not found in environment. Using demo key.")
    
    # Validate OpenRouter API key by making a simple request
    try:
        headers = {
            "Authorization": f"Bearer {openrouter_api_key}",
            "HTTP-Referer": "https://sharia-ai.om",
            "X-Title": "ShariaAI - Omani Legal Assistant"
        }
        # Make a simple request to test the API key
        response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
        if response.status_code != 200:
            logging.error(f"OpenRouter API key validation failed: {response.status_code} - {response.text}")
            # Use backup key if primary fails
            openrouter_api_key = "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"
            logging.warning("Using backup OpenRouter API key due to validation failure.")
    except Exception as e:
        logging.error(f"Error validating OpenRouter API key: {e}")
        # Keep the key as is, we'll handle errors at usage time
    
    if not llamaindex_api_key:
        llamaindex_api_key = "llx-gtcRZJSsolYe3nOrX80tXf5cMySyp2K4KdCd14HbWcTor3jz"
        logging.warning("LLAMAINDEX_API_KEY not found in environment. Using default key.")
    
    if not legal_files_dir:
        legal_files_dir = "/Users/faisalalanqoudi/anka-project/data"
        logging.warning("LEGAL_FILES_DIR not found in environment. Using default directory.")
    
    return {
        "openrouter_api_key": openrouter_api_key,
        "llamaindex_api_key": llamaindex_api_key,
        "legal_files_dir": legal_files_dir
    }
