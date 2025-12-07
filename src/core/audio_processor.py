# src/core/audio_processor.py
"""
Audio File Processing Utilities
================================
Handles audio format conversion, validation, and preprocessing

Why we need this:
- Whisper works best with specific formats (16kHz, mono, WAV)
- Users upload various formats (MP3, M4A, etc.)
- Need to validate files before processing (size, duration, format)
"""

from pydub import AudioSegment
from pathlib import Path
import logging
from typing import Optional, Tuple, Dict, List
import os

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Audio file processing and validation utilities"""
    
    # Supported formats
    SUPPORTED_FORMATS = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.wma', '.aac']
    
    # Limits
    MAX_FILE_SIZE_MB = 500
    MAX_DURATION_HOURS = 3
    MIN_DURATION_SECONDS = 1
    
    # Optimal settings for Whisper
    WHISPER_SAMPLE_RATE = 16000  # 16kHz
    WHISPER_CHANNELS = 1          # Mono
    
    @staticmethod
    def validate_audio_file(file_path: str) -> Tuple[bool, str]:
        """
        Validate audio file
        
        Checks:
        - File exists
        - Supported format
        - File size within limits
        - Duration within limits
        - File can be loaded
        
        Args:
            file_path: Path to audio file
        
        Returns:
            (is_valid: bool, message: str)
        
        Example:
            is_valid, msg = AudioProcessor.validate_audio_file("meeting.mp3")
            if not is_valid:
                print(f"Invalid: {msg}")
        """
        path = Path(file_path)
        
        # Check 1: File exists
        if not path.exists():
            return False, f"File does not exist: {file_path}"
        
        # Check 2: File extension
        if path.suffix.lower() not in AudioProcessor.SUPPORTED_FORMATS:
            return False, (
                f"Unsupported format '{path.suffix}'. "
                f"Supported: {', '.join(AudioProcessor.SUPPORTED_FORMATS)}"
            )
        
        # Check 3: File size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > AudioProcessor.MAX_FILE_SIZE_MB:
            return False, (
                f"File too large: {size_mb:.1f}MB "
                f"(maximum: {AudioProcessor.MAX_FILE_SIZE_MB}MB)"
            )
        
        # Check 4: Can load audio
        try:
            audio = AudioSegment.from_file(str(path))
            duration_seconds = len(audio) / 1000  # milliseconds to seconds
            
            # Check 5: Duration limits
            if duration_seconds < AudioProcessor.MIN_DURATION_SECONDS:
                return False, (
                    f"Audio too short: {duration_seconds:.1f}s "
                    f"(minimum: {AudioProcessor.MIN_DURATION_SECONDS}s)"
                )
            
            max_duration_seconds = AudioProcessor.MAX_DURATION_HOURS * 3600
            if duration_seconds > max_duration_seconds:
                return False, (
                    f"Audio too long: {duration_seconds/3600:.1f}h "
                    f"(maximum: {AudioProcessor.MAX_DURATION_HOURS}h)"
                )
            
            logger.info(f"✅ Valid audio: {path.name} ({size_mb:.1f}MB, {duration_seconds:.1f}s)")
            return True, f"Valid audio file ({size_mb:.1f}MB, {duration_seconds:.1f}s)"
            
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            return False, f"Failed to load audio file: {str(e)}"
    
    @staticmethod
    def convert_to_wav(
        input_path: str,
        output_path: Optional[str] = None,
        optimize_for_whisper: bool = True
    ) -> str:
        """
        Convert audio to WAV format
        
        Args:
            input_path: Input audio file
            output_path: Output path (optional, auto-generated if None)
            optimize_for_whisper: Convert to Whisper's preferred format (16kHz, mono)
        
        Returns:
            Path to converted WAV file
        
        Example:
            wav_path = AudioProcessor.convert_to_wav("meeting.mp3")
            # Creates: meeting.wav (16kHz, mono)
        """
        logger.info(f"Converting audio: {input_path}")
        
        try:
            # Load audio (pydub auto-detects format)
            audio = AudioSegment.from_file(input_path)
            
            # Optimize for Whisper if requested
            if optimize_for_whisper:
                logger.info("Optimizing for Whisper (16kHz, mono)")
                audio = audio.set_frame_rate(AudioProcessor.WHISPER_SAMPLE_RATE)
                audio = audio.set_channels(AudioProcessor.WHISPER_CHANNELS)
            
            # Determine output path
            if output_path is None:
                input_path_obj = Path(input_path)
                output_path = str(input_path_obj.with_suffix('.wav'))
            
            # Export as WAV
            audio.export(
                output_path,
                format="wav",
                parameters=["-ac", "1"]  # Force mono
            )
            
            output_size = Path(output_path).stat().st_size / (1024 * 1024)
            logger.info(f"✅ Converted to WAV: {output_path} ({output_size:.1f}MB)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise Exception(f"Failed to convert audio: {str(e)}")
    
    @staticmethod
    def get_audio_info(file_path: str) -> Dict:
        """
        Get detailed audio file information
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Dictionary with audio properties
        
        Example:
            info = AudioProcessor.get_audio_info("meeting.mp3")
            print(f"Duration: {info['duration']}s")
            print(f"Sample rate: {info['sample_rate']}Hz")
        """
        try:
            path = Path(file_path)
            audio = AudioSegment.from_file(str(path))
            
            info = {
                "duration": len(audio) / 1000,  # seconds
                "sample_rate": audio.frame_rate,  # Hz
                "channels": audio.channels,
                "sample_width": audio.sample_width,  # bytes
                "format": path.suffix.lstrip('.'),
                "size_mb": path.stat().st_size / (1024 * 1024),
                "bitrate": audio.frame_rate * audio.channels * audio.sample_width * 8 / 1000  # kbps
            }
            
            logger.info(f"Audio info for {path.name}: {info['duration']:.1f}s, {info['sample_rate']}Hz")
            return info
            
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            raise
    
    @staticmethod
    def split_long_audio(
        file_path: str,
        chunk_duration_minutes: int = 30,
        output_dir: Optional[str] = None
    ) -> List[str]:
        """
        Split long audio into chunks
        
        Useful for very long meetings (2+ hours) to:
        - Process in parallel
        - Avoid memory issues
        - Better error handling (if one chunk fails, others succeed)
        
        Args:
            file_path: Input audio file
            chunk_duration_minutes: Size of each chunk in minutes
            output_dir: Output directory (default: same as input)
        
        Returns:
            List of chunk file paths
        
        Example:
            chunks = AudioProcessor.split_long_audio("long_meeting.wav", 30)
            # Creates: long_meeting_chunk_0.wav, long_meeting_chunk_1.wav, ...
        """
        logger.info(f"Splitting audio: {file_path} into {chunk_duration_minutes}min chunks")
        
        try:
            audio = AudioSegment.from_file(file_path)
            chunk_length_ms = chunk_duration_minutes * 60 * 1000
            
            path = Path(file_path)
            if output_dir is None:
                output_dir = path.parent
            else:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            chunks = []
            chunk_index = 0
            
            for chunk_start in range(0, len(audio), chunk_length_ms):
                chunk = audio[chunk_start:chunk_start + chunk_length_ms]
                
                chunk_path = Path(output_dir) / f"{path.stem}_chunk_{chunk_index}{path.suffix}"
                chunk.export(
                    str(chunk_path),
                    format=path.suffix.lstrip('.')
                )
                
                chunks.append(str(chunk_path))
                logger.info(f"  Created chunk {chunk_index}: {chunk_path.name}")
                chunk_index += 1
            
            logger.info(f"✅ Split into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to split audio: {e}")
            raise
    
    @staticmethod
    def extract_audio_segment(
        file_path: str,
        start_seconds: float,
        end_seconds: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extract a segment from audio file
        
        Args:
            file_path: Input audio file
            start_seconds: Start time in seconds
            end_seconds: End time in seconds
            output_path: Output path (optional)
        
        Returns:
            Path to extracted segment
        
        Example:
            # Extract 30s-60s segment
            segment = AudioProcessor.extract_audio_segment(
                "meeting.wav",
                start_seconds=30,
                end_seconds=60
            )
        """
        try:
            audio = AudioSegment.from_file(file_path)
            
            # Convert to milliseconds
            start_ms = int(start_seconds * 1000)
            end_ms = int(end_seconds * 1000)
            
            # Extract segment
            segment = audio[start_ms:end_ms]
            
            # Determine output path
            if output_path is None:
                path = Path(file_path)
                output_path = str(path.parent / f"{path.stem}_segment_{start_seconds}_{end_seconds}{path.suffix}")
            
            # Export
            segment.export(output_path, format=Path(file_path).suffix.lstrip('.'))
            
            logger.info(f"✅ Extracted segment: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to extract segment: {e}")
            raise
    
    @staticmethod
    def normalize_audio(file_path: str, target_dBFS: float = -20.0) -> str:
        """
        Normalize audio volume
        
        Useful for:
        - Consistent volume levels
        - Better transcription accuracy
        
        Args:
            file_path: Input audio file
            target_dBFS: Target loudness (default: -20 dBFS)
        
        Returns:
            Path to normalized file (overwrites original)
        """
        try:
            audio = AudioSegment.from_file(file_path)
            
            # Calculate change needed
            change_in_dBFS = target_dBFS - audio.dBFS
            
            # Normalize
            normalized = audio.apply_gain(change_in_dBFS)
            
            # Overwrite
            normalized.export(file_path, format=Path(file_path).suffix.lstrip('.'))
            
            logger.info(f"✅ Normalized audio: {file_path} (adjusted by {change_in_dBFS:.1f} dB)")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to normalize audio: {e}")
            raise

# ============================================
# SINGLETON
# ============================================

_audio_processor: Optional[AudioProcessor] = None

def get_audio_processor() -> AudioProcessor:
    """Get audio processor (singleton)"""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
    return _audio_processor