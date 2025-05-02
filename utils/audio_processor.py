"""Audio processing module for ShariaAI - Voice transcription for legal queries."""
import os
import tempfile
import streamlit as st
import numpy as np
import whisper
import time
import queue
from threading import Thread
import av
import logging
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
from utils.env_loader import load_env_vars

# Load environment variables
env_vars = load_env_vars()
OPENROUTER_API_KEY = env_vars['openrouter_api_key']

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
        """Record audio from the microphone and transcribe it using WebRTC."""
        st.write("Recording audio... Speak your legal query")
        
        # Create a queue to store audio frames
        audio_frames = queue.Queue()
        recording_started = False
        recording_stopped = False
        transcription_result = [None]  # Use a list to store the result across callbacks
        
        # Define callback functions for WebRTC
        def video_frame_callback(frame):
            # Just return the frame, we don't process video
            return frame
        
        def audio_frame_callback(frame):
            nonlocal recording_started
            # Mark that we've started recording
            recording_started = True
            # Add the audio frame to the queue
            audio_frames.put(frame)
            return frame
        
        # Configure WebRTC
        rtc_config = RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )
        
        # Create the WebRTC streamer
        webrtc_ctx = webrtc_streamer(
            key="voice-query",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=rtc_config,
            video_frame_callback=video_frame_callback,
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={"video": False, "audio": True},
        )
        
        if webrtc_ctx.state.playing:
            st.info("Recording... Speak your legal query and then click 'Stop' when finished.")
        
        # When the user stops the recording
        if not webrtc_ctx.state.playing and recording_started and not recording_stopped:
            st.success("Recording stopped. Processing audio...")
            recording_stopped = True
            
            # Save all audio frames to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_filename = f.name
                
                # Convert the frames to a WAV file
                try:
                    # Get all frames from the queue
                    frames = []
                    while not audio_frames.empty():
                        frames.append(audio_frames.get())
                    
                    if frames:
                        # Create a new audio container
                        container = av.open(temp_filename, mode='w')
                        stream = container.add_stream('pcm_s16le', rate=48000, channels=1)
                        
                        # Write the frames to the container
                        for frame in frames:
                            for packet in stream.encode(frame):
                                container.mux(packet)
                        
                        # Close the container
                        container.close()
                        
                        # Transcribe the recorded audio
                        transcription = self.transcribe_audio(temp_filename)
                        transcription_result[0] = transcription
                        
                        # Display the audio for playback
                        with open(temp_filename, "rb") as audio_file:
                            audio_bytes = audio_file.read()
                            st.audio(audio_bytes, format="audio/wav")
                except Exception as e:
                    st.error(f"Error processing audio: {str(e)}")
                    logging.error(f"Error processing audio: {str(e)}")
                finally:
                    # Clean up the temporary file
                    try:
                        os.unlink(temp_filename)
                    except:
                        pass
        
        return transcription_result[0]
    
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
        st.subheader("Voice Query")
        st.write("Use the microphone below to record your legal question")
        
        # Record audio and get transcription directly
        transcription = self.record_and_transcribe()
        
        if transcription:
            st.success("Transcription successful!")
            st.write(f"**Your question**: {transcription}")
        
        return transcription
