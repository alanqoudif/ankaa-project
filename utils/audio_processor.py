"""Audio processing module for ShariaAI - Voice transcription for legal queries."""
import os
import tempfile
import streamlit as st
import numpy as np
import whisper
from pydub import AudioSegment
from utils.env_loader import load_env_vars

# Load environment variables
_, _, OPENROUTER_API_KEY, _ = load_env_vars()

class AudioProcessor:
    """Handles audio recording, processing, and transcription for voice queries."""
    
    def __init__(self):
        """Initialize the audio processor with local Whisper model."""
        self.sample_rate = 16000
        self.whisper_model = None  # Lazy-loaded
    
    def _load_whisper_model(self):
        """Load the Whisper model if not already loaded."""
        if self.whisper_model is None:
            with st.spinner("Loading Whisper model..."):
                self.whisper_model = whisper.load_model("base")
        return self.whisper_model
    
    def transcribe_audio(self, audio_file_path):
        """Transcribe audio using Whisper model."""
        try:
            # Load the Whisper model
            model = self._load_whisper_model()
            
            # Transcribe the audio
            result = model.transcribe(audio_file_path)
            
            # Return the transcribed text
            return result["text"]
            
        except Exception as e:
            st.error(f"Error transcribing audio: {str(e)}")
            return ""
    
    def record_and_transcribe(self):
        """Record audio from the microphone and transcribe it."""
        st.write("📝 Recording audio... Speak your legal query")
        
        # Use streamlit's audio recorder component
        audio_bytes = st.audio_recorder()
        
        if audio_bytes is not None:
            st.audio(audio_bytes, format="audio/wav")
            st.success("✅ Audio recorded successfully!")
            
            with st.spinner("Transcribing audio..."):
                # Process and transcribe the audio
                audio_path = self.preprocess_audio(audio_bytes)
                if audio_path:
                    transcription = self.transcribe_audio(audio_path)
                    # Clean up temp file
                    os.unlink(audio_path)
                    
                    if transcription:
                        st.success("✅ Transcription complete!")
                        return transcription
        
        return None
    
    def detect_language(self, audio_file_path):
        """Detect the language of audio using Whisper."""
        try:
            # Load the Whisper model
            model = self._load_whisper_model()
            
            # Detect the language
            audio = whisper.load_audio(audio_file_path)
            audio = whisper.pad_or_trim(audio)
            
            # Make log-Mel spectrogram and move to the same device as the model
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            
            # Detect the spoken language
            _, probs = model.detect_language(mel)
            language = max(probs, key=probs.get)
            
            return language
        except Exception as e:
            st.error(f"Error detecting language: {str(e)}")
            return None
    
    def get_voice_query(self):
        """Interface for getting a voice query from the user."""
        transcription = None
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write("Click the button to record your legal question")
        
        with col2:
            if st.button("🎤 Record"):
                transcription = self.record_and_transcribe()
        
        if transcription:
            st.info(f"**Transcription**: {transcription}")
        
        return transcription
