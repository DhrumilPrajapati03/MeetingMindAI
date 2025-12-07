# scripts/test_audio.py
"""Test audio processing utilities"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.audio_processor import AudioProcessor
from pydub.generators import Sine
from pydub import AudioSegment
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_audio(filename: str = "test_audio.wav", duration_seconds: int = 5):
    """Create a test audio file"""
    logger.info(f"Creating test audio: {filename} ({duration_seconds}s)")
    
    # Generate sine wave (440 Hz = A note)
    sine_wave = Sine(440).to_audio_segment(duration=duration_seconds * 1000)
    
    # Export
    output_path = Path("data") / "uploads" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    sine_wave.export(str(output_path), format="wav")
    logger.info(f"✅ Created: {output_path}")
    
    return str(output_path)

def test_audio_processor():
    """Test audio processing functions"""
    logger.info("=" * 50)
    logger.info("Testing Audio Processor")
    logger.info("=" * 50)
    
    # Create test audio
    test_file = create_test_audio("test_meeting.wav", duration_seconds=10)
    
    # Test 1: Validate
    logger.info("\n1. Testing validation...")
    is_valid, msg = AudioProcessor.validate_audio_file(test_file)
    logger.info(f"   Valid: {is_valid}")
    logger.info(f"   Message: {msg}")
    assert is_valid, f"Validation failed: {msg}"
    
    # Test 2: Get info
    logger.info("\n2. Testing get_audio_info...")
    info = AudioProcessor.get_audio_info(test_file)
    logger.info(f"   Duration: {info['duration']:.1f}s")
    logger.info(f"   Sample rate: {info['sample_rate']}Hz")
    logger.info(f"   Channels: {info['channels']}")
    logger.info(f"   Size: {info['size_mb']:.2f}MB")
    
    # Test 3: Convert to WAV (optimized for Whisper)
    logger.info("\n3. Testing convert_to_wav...")
    wav_path = AudioProcessor.convert_to_wav(test_file)
    logger.info(f"   ✅ Converted: {wav_path}")
    
    # Verify conversion
    converted_info = AudioProcessor.get_audio_info(wav_path)
    logger.info(f"   New sample rate: {converted_info['sample_rate']}Hz (should be 16000)")
    logger.info(f"   New channels: {converted_info['channels']} (should be 1)")
    
    assert converted_info['sample_rate'] == 16000, "Sample rate not 16kHz"
    assert converted_info['channels'] == 1, "Not mono"
    
    # Test 4: Extract segment
    logger.info("\n4. Testing extract_audio_segment...")
    segment_path = AudioProcessor.extract_audio_segment(
        test_file,
        start_seconds=2,
        end_seconds=5
    )
    logger.info(f"   ✅ Extracted: {segment_path}")
    
    segment_info = AudioProcessor.get_audio_info(segment_path)
    logger.info(f"   Segment duration: {segment_info['duration']:.1f}s (should be ~3s)")
    
    # Test 5: Invalid file
    logger.info("\n5. Testing invalid file...")
    is_valid, msg = AudioProcessor.validate_audio_file("nonexistent.wav")
    logger.info(f"   Valid: {is_valid} (should be False)")
    logger.info(f"   Message: {msg}")
    assert not is_valid, "Should be invalid"
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ All audio processing tests passed!")
    logger.info("=" * 50)

if __name__ == "__main__":
    try:
        test_audio_processor()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        sys.exit(1)