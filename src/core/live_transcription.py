# src/core/live_transcription.py
"""
Live Transcription Service
===========================
Real-time audio transcription using Whisper
"""

import whisper
import torch
import numpy as np
import base64
import logging
from typing import Optional, Dict
from datetime import datetime
import asyncio
from collections import deque
import io
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class LiveTranscriptionService:
    """
    Service for real-time audio transcription
    
    How it works:
    1. Receives audio chunks from WebSocket
    2. Buffers chunks until enough data (3-5 seconds)
    3. Transcribes buffered audio with Whisper
    4. Returns transcript incrementally
    5. Maintains full transcript in memory
    """
    
    def __init__(self, session_id: str, language: str = "en", meeting_id: Optional[int] = None):
        """
        Initialize live transcription service
        
        Args:
            session_id: Unique session identifier
            language: Language code (en, es, fr, etc.)
            meeting_id: Associated meeting ID
        """
        self.session_id = session_id
        self.language = language
        self.meeting_id = meeting_id
        
        # Load Whisper model (use 'base' for speed)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Whisper model on {self.device}...")
        self.model = whisper.load_model("base", device=self.device)
        
        # Audio buffer
        self.audio_buffer = deque(maxlen=100)  # Store last 100 chunks
        self.buffer_duration = 0.0  # seconds
        self.min_buffer_duration = 3.0  # Process every 3 seconds
        
        # Transcription state
        self.full_transcript = []
        self.last_transcript_time = datetime.utcnow()
        self.start_time = datetime.utcnow()
        
        logger.info(f"✅ Live transcription service initialized: {session_id}")
    
    async def process_audio_chunk(self, audio_data_base64: str) -> Optional[Dict]:
        """
        Process incoming audio chunk
        
        Args:
            audio_data_base64: Base64 encoded audio data (PCM 16-bit, 16kHz, mono)
        
        Returns:
            Transcript dict if ready, None if buffering
        """
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data_base64)
            
            # Convert to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Add to buffer
            self.audio_buffer.append(audio_array)
            
            # Update buffer duration (assuming 16kHz sample rate)
            chunk_duration = len(audio_array) / 16000.0
            self.buffer_duration += chunk_duration
            
            # Check if we have enough audio to transcribe
            if self.buffer_duration >= self.min_buffer_duration:
                # Concatenate buffer
                audio_full = np.concatenate(list(self.audio_buffer))
                
                # Transcribe
                result = await self._transcribe_audio(audio_full)
                
                # Clear buffer
                self.audio_buffer.clear()
                self.buffer_duration = 0.0
                
                return result
            
            return None
        
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None
    
    async def _transcribe_audio(self, audio: np.ndarray) -> Dict:
        """
        Transcribe audio array with Whisper
        
        Args:
            audio: NumPy array of audio samples
        
        Returns:
            Transcript result
        """
        try:
            # Run Whisper in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._whisper_transcribe,
                audio
            )
            
            text = result["text"].strip()
            
            if text:
                # Add to full transcript
                self.full_transcript.append({
                    "text": text,
                    "timestamp": datetime.utcnow().isoformat(),
                    "offset": (datetime.utcnow() - self.start_time).total_seconds()
                })
                
                logger.info(f"📝 Transcribed: {text[:50]}...")
                
                return {
                    "text": text,
                    "is_final": True,
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": 1.0
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def _whisper_transcribe(self, audio: np.ndarray) -> Dict:
        """
        Synchronous Whisper transcription
        
        Args:
            audio: Audio samples
        
        Returns:
            Whisper result
        """
        result = self.model.transcribe(
            audio,
            language=self.language,
            fp16=False if self.device == "cpu" else True,
            verbose=False
        )
        
        return result
    
    async def finalize(self) -> Dict:
        """
        Finalize transcription session
        
        Returns:
            Final transcript and metadata
        """
        # Process any remaining buffer
        if self.audio_buffer and self.buffer_duration > 0:
            audio_full = np.concatenate(list(self.audio_buffer))
            result = await self._transcribe_audio(audio_full)
        
        # Combine all transcript segments
        full_text = " ".join([segment["text"] for segment in self.full_transcript])
        
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        logger.info(f"✅ Finalized session {self.session_id}: {len(full_text)} chars, {duration:.1f}s")
        
        return {
            "full_transcript": full_text,
            "segments": self.full_transcript,
            "duration": duration,
            "word_count": len(full_text.split())
        }