# src/core/transcription.py
"""
Batch Audio Transcription Service
==================================
Uses OpenAI Whisper for speech-to-text conversion

Whisper Model Sizes:
- tiny:   Fast, lowest accuracy (~1GB RAM, 32x realtime on CPU)
- base:   Good balance (~1GB RAM, 16x realtime) ← We use this
- small:  Better accuracy (~2GB RAM, 6x realtime)
- medium: High accuracy (~5GB RAM, 2x realtime)
- large:  Best accuracy (~10GB RAM, 1x realtime, needs GPU)

For Day 2, we'll use 'base' model - good balance of speed/accuracy
"""

import whisper
import torch
from typing import Dict, List, Optional
import time
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class TranscriptionService:
    """
    Batch audio transcription using OpenAI Whisper
    
    Features:
    - Automatic language detection
    - Timestamp generation
    - Multiple output formats
    - GPU acceleration (if available)
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper model
        
        Args:
            model_size: Model size (tiny/base/small/medium/large)
        """
        # Detect device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🎙️ Transcription device: {self.device}")
        
        # Windows optimization
        if os.name == 'nt':  # Windows
            torch.set_num_threads(4)
        
        logger.info(f"Loading Whisper '{model_size}' model...")
        start_time = time.time()
        
        # Load model
        self.model = whisper.load_model(model_size, device=self.device)
        
        load_time = time.time() - start_time
        logger.info(f"✅ Model loaded in {load_time:.2f}s")
        
        self.model_size = model_size
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = "en",
        task: str = "transcribe"
    ) -> Dict:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            language: Language code ("en", "es", "fr", etc.) or None for auto-detect
            task: "transcribe" or "translate" (translate to English)
        
        Returns:
            {
                "text": "Full transcript text...",
                "segments": [...],  # Detailed segments with timestamps
                "language": "en",
                "duration": 123.45,
                "processing_time": 45.67,
                "model": "base"
            }
        
        Example:
            service = TranscriptionService()
            result = service.transcribe("meeting.wav")
            print(result["text"])
        """
        logger.info(f"🎙️ Transcribing: {Path(audio_path).name}")
        start_time = time.time()
        
        try:
            # Transcribe
            result = self.model.transcribe(
                audio_path,
                language=language,
                task=task,
                fp16=False if self.device == "cpu" else True,  # Use FP16 on GPU
                verbose=False,  # Don't print progress
                word_timestamps=False  # Set True for word-level timestamps (slower)
            )
            
            processing_time = time.time() - start_time
            
            # Calculate duration from segments
            duration = 0
            if result.get("segments"):
                duration = result["segments"][-1]["end"]
            
            # Real-time factor (how much faster than real-time)
            rtf = processing_time / duration if duration > 0 else 0
            
            logger.info(
                f"✅ Transcription complete: {duration:.1f}s audio in {processing_time:.1f}s "
                f"(RTF: {rtf:.2f}x)"
            )
            
            return {
                "text": result["text"].strip(),
                "segments": result["segments"],
                "language": result.get("language", language),
                "duration": duration,
                "processing_time": processing_time,
                "model": self.model_size,
                "word_count": len(result["text"].split()),
                "rtf": rtf
            }
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise Exception(f"Transcription failed: {str(e)}")
    
    def transcribe_with_timestamps(self, audio_path: str) -> List[Dict]:
        """
        Transcribe with formatted timestamps for display
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            [
                {
                    "start": 0.0,
                    "end": 5.2,
                    "text": "Hello everyone, welcome to the meeting.",
                    "speaker": "Unknown"  # Placeholder (speaker diarization later)
                },
                ...
            ]
        
        Example:
            segments = service.transcribe_with_timestamps("meeting.wav")
            for seg in segments:
                print(f"[{seg['start']:.1f}s] {seg['text']}")
        """
        logger.info(f"🎙️ Transcribing with timestamps: {Path(audio_path).name}")
        
        result = self.transcribe(audio_path)
        
        formatted_segments = []
        for segment in result["segments"]:
            formatted_segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "speaker": "Unknown",  # TODO: Add speaker diarization
                "confidence": segment.get("avg_logprob", 0)
            })
        
        logger.info(f"✅ Generated {len(formatted_segments)} timestamped segments")
        return formatted_segments
    
    def transcribe_multiple(self, audio_paths: List[str]) -> List[Dict]:
        """
        Transcribe multiple audio files
        
        Args:
            audio_paths: List of audio file paths
        
        Returns:
            List of transcription results
        """
        results = []
        
        for i, audio_path in enumerate(audio_paths, 1):
            logger.info(f"Processing {i}/{len(audio_paths)}: {Path(audio_path).name}")
            
            try:
                result = self.transcribe(audio_path)
                result["file_path"] = audio_path
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to transcribe {audio_path}: {e}")
                results.append({
                    "file_path": audio_path,
                    "error": str(e),
                    "text": None
                })
        
        logger.info(f"✅ Transcribed {len(results)} files")
        return results
    
    @staticmethod
    def estimate_processing_time(duration_seconds: float, model_size: str = "base") -> float:
        """
        Estimate how long transcription will take
        
        Args:
            duration_seconds: Audio duration
            model_size: Whisper model size
        
        Returns:
            Estimated processing time in seconds
        """
        # RTF estimates on CPU (approximate)
        rtf_map = {
            "tiny": 0.03,    # 32x realtime
            "base": 0.06,    # 16x realtime
            "small": 0.16,   # 6x realtime
            "medium": 0.5,   # 2x realtime
            "large": 1.0     # 1x realtime
        }
        
        rtf = rtf_map.get(model_size, 0.06)
        return duration_seconds * rtf

# ============================================
# SINGLETON
# ============================================

_transcription_service: Optional[TranscriptionService] = None

def get_transcription_service(model_size: str = "base") -> TranscriptionService:
    """
    Get transcription service (singleton)
    
    Usage:
        from src.core.transcription import get_transcription_service
        
        service = get_transcription_service()
        result = service.transcribe("meeting.wav")
    """
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService(model_size=model_size)
    return _transcription_service