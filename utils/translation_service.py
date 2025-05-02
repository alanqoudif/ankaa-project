"""
Translation service for ShariaAI that uses the same AI model for translations across the application.
This ensures consistency between the chat interface and other parts of the application.
"""
import streamlit as st
from typing import Optional
from utils.env_loader import load_env_vars
import logging
import openai
from openai import OpenAI

# Load environment variables
env_vars = load_env_vars()
OPENROUTER_API_KEY = env_vars.get('openrouter_api_key')

class TranslationService:
    """Provides AI-powered translation services throughout the application."""
    
    def __init__(self):
        """Initialize the translation service with the OpenAI model."""
        self.client = None
        self.model = "qwen/qwen1.5-110b"  # Using the same model as the chat interface
        
        # Initialize the client using the OpenRouter API
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the OpenAI client with appropriate configuration."""
        try:
            if not OPENROUTER_API_KEY:
                st.error("OpenRouter API key not found. Translation features will not work.")
                return
                
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY,
                headers={
                    "HTTP-Referer": "https://sharia-ai.om",  # Replace with your actual website
                    "X-Title": "ShariaAI - Omani Legal Assistant"
                }
            )
        except Exception as e:
            st.error(f"Error initializing translation service: {str(e)}")
            logging.error(f"Translation service initialization error: {str(e)}", exc_info=True)
    
    def translate(self, text: str, target_language: str = "Arabic", source_language: Optional[str] = None) -> str:
        """
        Translate text to the target language using AI.
        
        Args:
            text: Text to translate
            target_language: Language to translate to ("Arabic" or "English")
            source_language: Source language (optional, AI will detect if not provided)
            
        Returns:
            Translated text, or original text if translation fails
        """
        if not text or not text.strip():
            return text
            
        if not self.client:
            st.warning("Translation service not available. Using original text.")
            return text
            
        try:
            # Determine direction for better prompt
            if source_language is None:
                # Try to detect if it's primarily Arabic or English
                arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
                if arabic_chars > len(text) / 2:
                    source_language = "Arabic"
                else:
                    source_language = "English"
            
            # Don't translate if source and target are the same
            if source_language == target_language:
                return text
            
            # Create appropriate prompt based on languages
            if target_language == "Arabic" and source_language == "English":
                prompt = (
                    f"Translate the following English text to Arabic. Ensure the translation is accurate, "
                    f"natural-sounding Arabic with correct legal terminology:\n\n{text}"
                )
            elif target_language == "English" and source_language == "Arabic":
                prompt = (
                    f"Translate the following Arabic text to English. Ensure the translation is accurate, "
                    f"natural-sounding English with correct legal terminology:\n\n{text}"
                )
            else:
                prompt = f"Translate this text from {source_language} to {target_language}: {text}"
            
            # Call the API for translation
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional legal translator specializing in Omani legal documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Keep temperature low for consistent translations
                max_tokens=1024
            )
            
            # Extract the translated text
            translated_text = response.choices[0].message.content
            
            # If successful, return the translation
            if translated_text and translated_text.strip():
                return translated_text.strip()
            else:
                # Fallback to original if empty response
                return text
                
        except Exception as e:
            logging.error(f"Translation error: {str(e)}", exc_info=True)
            st.error(f"Translation error: {str(e)}")
            # Return original text on error
            return text
    
    def translate_to_arabic(self, text: str) -> str:
        """Convenience method to translate text to Arabic."""
        return self.translate(text, target_language="Arabic", source_language="English")
    
    def translate_to_english(self, text: str) -> str:
        """Convenience method to translate text to English."""
        return self.translate(text, target_language="English", source_language="Arabic")

# Use a lazy-loading approach to prevent initialization at import time
_translation_service_instance = None

def get_translation_service():
    """Get the translation service singleton instance with lazy loading."""
    global _translation_service_instance
    try:
        if _translation_service_instance is None:
            logging.info("Initializing translation service for the first time")
            _translation_service_instance = TranslationService()
        return _translation_service_instance
    except Exception as e:
        logging.error(f"Error getting translation service: {e}", exc_info=True)
        # Return a dummy service with minimal functionality in case of failure
        return _DummyTranslationService()

class _DummyTranslationService:
    """A fallback translation service that simply returns the original text.
    Used when the main translation service fails to initialize or encounters errors."""
    
    def __init__(self):
        logging.warning("Using dummy translation service as fallback")
    
    def translate(self, text, target_language=None, source_language=None):
        """Return the original text without translation."""
        return text
    
    def translate_to_arabic(self, text):
        """Return the original text (if it's already Arabic) or a simple Arabic placeholder."""
        # Check if text appears to be in English (basic check)
        if any(ord(c) < 128 for c in text):
            return "النص المترجم غير متوفر" + " " + text
        return text
    
    def translate_to_english(self, text):
        """Return the original text (if it's already English) or a simple English placeholder."""
        # Check if text contains Arabic characters
        if any(ord(c) > 1536 and ord(c) < 1791 for c in text):
            return "Translation unavailable: " + text
        return text

# Provide a reference to the singleton getter
translation_service = get_translation_service
