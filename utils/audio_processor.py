"""Audio processing module for ShariaAI - Voice transcription for legal queries."""
import os
import time
import queue
import wave
import tempfile
import pyaudio
import logging
from typing import List, Dict, Any, Optional
from threading import Thread

import av
import numpy as np
import streamlit as st
import whisper
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
        recording_started = [False]  # Using list to modify in nested function
        recording_complete = [False]  # Flag to indicate recording is complete
        transcription_result = [None]  # Use a list to store the result across callbacks
        
        # Define callback functions for WebRTC
        def video_frame_callback(frame):
            # Just return the frame, we don't process video
            return frame
        
        def audio_frame_callback(frame):
            # Mark that we've started recording
            recording_started[0] = True
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
            async_processing=True,
        )
        
        # Instructions to the user
        if webrtc_ctx.state.playing:
            st.info("🎤 Recording... Speak your legal query and then click 'Stop' when finished.")
        
        # Create a placeholder for the transcription status
        status_placeholder = st.empty()
        
        # Create a process button to handle audio processing separately from WebRTC stream
        process_button = st.button("Process Recording", disabled=not recording_started[0] or recording_complete[0])
        
        # When the user explicitly requests processing
        if process_button or (recording_started[0] and not webrtc_ctx.state.playing and not recording_complete[0]):
            status_placeholder.info("Processing audio... This may take a moment.")
            recording_complete[0] = True
            
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
                        st.info(f"Processing {len(frames)} audio frames...")
                        
                        # Create a new audio container
                        container = av.open(temp_filename, mode='w')
                        stream = container.add_stream('pcm_s16le', rate=48000, channels=1)
                        
                        # Write the frames to the container
                        for frame in frames:
                            try:
                                for packet in stream.encode(frame):
                                    container.mux(packet)
                            except Exception as e:
                                st.warning(f"Skipped a frame: {str(e)}")
                        
                        # Flush any remaining packets
                        for packet in stream.encode(None):
                            container.mux(packet)
                        
                        # Close the container
                        container.close()
                        
                        # Check if the file was created successfully
                        if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                            # Display the audio for playback
                            with open(temp_filename, "rb") as audio_file:
                                audio_bytes = audio_file.read()
                                st.audio(audio_bytes, format="audio/wav")
                            
                            # Transcribe the recorded audio
                            status_placeholder.info("Transcribing audio with Whisper...")
                            transcription = self.transcribe_audio(temp_filename)
                            
                            if transcription and transcription.strip():
                                transcription_result[0] = transcription
                                status_placeholder.success("Transcription successful!")
                            else:
                                status_placeholder.error("Transcription failed. Please try again and speak clearly.")
                        else:
                            status_placeholder.error("Failed to create audio file. Please try again.")
                    else:
                        status_placeholder.warning("No audio recorded. Please try again.")
                except Exception as e:
                    status_placeholder.error(f"Error processing audio: {str(e)}")
                    logging.error(f"Error processing audio: {str(e)}")
                finally:
                    # Clean up the temporary file
                    try:
                        if os.path.exists(temp_filename):
                            os.unlink(temp_filename)
                    except Exception as cleanup_error:
                        logging.error(f"Error cleaning up temp file: {str(cleanup_error)}")
        
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
        st.write("Use the microphone below to record your legal question")
        
        # Create a session state for transcription if it doesn't exist
        if "transcription" not in st.session_state:
            st.session_state.transcription = None
            
        if "submit_ready" not in st.session_state:
            st.session_state.submit_ready = False
            
        # Function to update session state when transcription is ready
        def on_transcription_ready(text):
            if text and text.strip():
                st.session_state.transcription = text
                st.session_state.submit_ready = True
        
        # Record audio and get transcription
        transcription = self.record_and_transcribe()
        
        # If we got a new transcription, update session state
        if transcription and transcription.strip():
            on_transcription_ready(transcription)
        
        # Display current transcription from session state
        if st.session_state.transcription:
            st.success("Transcription successful!")
            st.write(f"**Your question**: {st.session_state.transcription}")
            
            # Process button - automatically processes the query
            if st.button("Process this question") or st.session_state.submit_ready:
                st.session_state.submit_ready = False  # Reset flag after use
                return st.session_state.transcription
        
        return None
    
    def chat_voice_recorder(self):
        """Simple voice recorder component for the chat interface that directly records audio and transcribes it."""
        # Initialize session state for voice recording
        if "voice_is_recording" not in st.session_state:
            st.session_state.voice_is_recording = False
        if "voice_transcription" not in st.session_state:
            st.session_state.voice_transcription = None
        
        # Simple record button that triggers audio recording
        if not st.session_state.voice_is_recording:
            # Show record button
            if st.button("🎤 Voice Input", key="voice_record_btn"):
                st.session_state.voice_is_recording = True
                st.rerun()
        else:
            # Show stop button
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("⏹️ Stop Recording", key="voice_stop_btn"):
                    st.session_state.voice_is_recording = False
                    # Record and transcribe audio
                    with st.spinner("Transcribing your audio..."):
                        # Use simple recording approach
                        audio_file = self.record_audio_simple()
                        if audio_file:
                            # Transcribe the audio file
                            transcription = self.transcribe_audio(audio_file)
                            # Clean up the temporary file
                            try:
                                os.unlink(audio_file)
                            except Exception:
                                pass
                            
                            if transcription and transcription.strip():
                                st.session_state.voice_transcription = transcription
                    st.rerun()
            
            with col2:
                st.markdown("🔴 **Recording...**")
        
        # Return the transcription
        return st.session_state.voice_transcription
    
    def record_audio_simple(self, duration=5):
        """Record audio using PyAudio directly without WebRTC.
        Returns the path to the recorded audio file."""
        try:
            # Create a temporary file for recording
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_filename = temp_file.name
            temp_file.close()
            
            # Set up PyAudio
            p = pyaudio.PyAudio()
            
            # Configure audio stream
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            # Collect audio data
            st.toast("Recording started...", icon="🎤")
            frames = []
            
            # Record for the specified duration (default 5 seconds)
            for i in range(0, int(16000 / 1024 * duration)):
                data = stream.read(1024)
                frames.append(data)
            
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            st.toast("Recording complete!", icon="✅")
            
            # Save the recorded audio to the temporary file
            wf = wave.open(temp_filename, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            return temp_filename
        except Exception as e:
            st.error(f"Error recording audio: {str(e)}")
            return None
    
    def _process_chat_audio(self):
        """Process audio frames from the chat recording and return transcription."""
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
                
                # Get all frames from the queue
                frames = []
                while not st.session_state.chat_audio_frames.empty():
                    frames.append(st.session_state.chat_audio_frames.get())
                
                if not frames:
                    return None
                
                # Create a new audio container
                container = av.open(temp_filename, mode='w')
                stream = container.add_stream('pcm_s16le', rate=48000, channels=1)
                
                # Write the frames to the container
                for frame in frames:
                    try:
                        for packet in stream.encode(frame):
                            container.mux(packet)
                    except Exception as e:
                        pass  # Skip problematic frames
                
                # Flush any remaining packets
                for packet in stream.encode(None):
                    container.mux(packet)
                
                # Close the container
                container.close()
                
                # Transcribe the audio
                if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                    # Transcribe the recorded audio
                    transcription = self.transcribe_audio(temp_filename)
                    return transcription
                
                return None
        except Exception as e:
            st.error(f"Error processing audio: {str(e)}")
            return None
        finally:
            # Clean up temporary file
            try:
                if 'temp_filename' in locals() and os.path.exists(temp_filename):
                    os.unlink(temp_filename)
            except Exception:
                pass
