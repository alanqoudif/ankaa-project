import whisper  # openai-whisper
import os
import tempfile

# API key
OPENROUTER_API_KEY = "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"

def transcribe_audio(audio_file_path, use_whisper=True):
    """Transcribe audio using Whisper API or local Whisper model."""
    try:
        if use_whisper:
            # Load the Whisper model
            model = whisper.load_model("base")
            
            # Transcribe the audio
            result = model.transcribe(audio_file_path)
            
            # Return the transcribed text
            return result["text"]
        else:
            # Fallback to Vosk in future implementation
            raise NotImplementedError("Vosk implementation is not available yet")
    
    except Exception as e:
        raise Exception(f"Error transcribing audio: {str(e)}")

def detect_language(audio_file_path):
    """Detect the language of audio using Whisper."""
    try:
        # Load the Whisper model
        model = whisper.load_model("base")
        
        # Detect the language
        audio = whisper.load_audio(audio_file_path)
        audio = whisper.pad_or_trim(audio)
        
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        _, probs = model.detect_language(mel)
        
        # Get the detected language
        detected_language = max(probs, key=probs.get)
        
        return detected_language
    
    except Exception as e:
        raise Exception(f"Error detecting language: {str(e)}")
