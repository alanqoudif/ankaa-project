from supabase.client import create_client
import os

# Supabase credentials - these would normally be stored in environment variables
# For demo purposes, using placeholder values
SUPABASE_URL = "https://your-supabase-project.supabase.co"
SUPABASE_KEY = "your-supabase-key"

def init_supabase():
    """Initialize Supabase client."""
    try:
        # Create Supabase client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    
    except Exception as e:
        raise Exception(f"Error initializing Supabase client: {str(e)}")

def save_chat_history(user_id, messages):
    """Save chat history to Supabase."""
    try:
        supabase = init_supabase()
        
        # Save chat history to database
        response = supabase.table("chat_history").insert({
            "user_id": user_id,
            "messages": messages,
            "created_at": "now()"
        }).execute()
        
        return response
    
    except Exception as e:
        raise Exception(f"Error saving chat history: {str(e)}")

def get_chat_history(user_id):
    """Get chat history from Supabase."""
    try:
        supabase = init_supabase()
        
        # Get chat history from database
        response = supabase.table("chat_history").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        return response.data
    
    except Exception as e:
        raise Exception(f"Error getting chat history: {str(e)}")

def save_generated_document(user_id, document_path, document_type, query):
    """Save generated document metadata to Supabase."""
    try:
        supabase = init_supabase()
        
        # Save document metadata to database
        response = supabase.table("generated_documents").insert({
            "user_id": user_id,
            "document_path": document_path,
            "document_type": document_type,
            "query": query,
            "created_at": "now()"
        }).execute()
        
        return response
    
    except Exception as e:
        raise Exception(f"Error saving document metadata: {str(e)}")

def get_user_documents(user_id):
    """Get user's generated documents from Supabase."""
    try:
        supabase = init_supabase()
        
        # Get user's documents from database
        response = supabase.table("generated_documents").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        return response.data
    
    except Exception as e:
        raise Exception(f"Error getting user documents: {str(e)}")
