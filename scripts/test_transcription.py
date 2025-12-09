# scripts/test_transcription.py
"""
Test Transcription Pipeline
============================
Tests the complete transcription workflow
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.transcriber import get_transcriber_agent
from src.core.audio_processor import get_audio_processor
from pydub.generators import Sine
from pydub import AudioSegment
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_audio():
    """Create a test audio file with speech"""
    logger.info("Creating test audio...")
    
    # For testing, we'll create a simple tone
    # In real use, you'd upload an actual meeting recording
    sine_wave = Sine(440).to_audio_segment(duration=10000)  # 10 seconds
    
    output_path = Path("data/uploads/test_transcription.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    sine_wave.export(str(output_path), format="wav")
    logger.info(f"✅ Created test audio: {output_path}")
    
    return str(output_path)

def test_transcription():
    """Test the transcription pipeline"""
    logger.info("=" * 60)
    logger.info("TESTING TRANSCRIPTION PIPELINE")
    logger.info("=" * 60)
    
    # Note: For a real test, you need an audio file with speech!
    # The sine wave won't transcribe to anything meaningful
    
    logger.info("""
⚠️  NOTE: This test uses a sine wave (tone) which won't produce a transcript.

To properly test transcription:
1. Record a short voice memo on your phone (30 seconds)
2. Save it as: data/uploads/real_meeting.wav
3. Run this script again with that file

For now, we'll test the pipeline flow...
""")
    
    # Create test audio
    test_audio = r"D:/MeetingMindAI/data/uploads/2021_04_07_JUME__34919016816___EMMA_ES___1617804854141.mp3"

    # Check if file exists
    if not Path(test_audio).exists():
        logger.error(f"❌ Audio file not found: {test_audio}")
        logger.info("Available files:")
        upload_dir = Path("data/uploads")
        if upload_dir.exists():
            for file in upload_dir.glob("*"):
                logger.info(f"  - {file.name}")
        sys.exit(1)

    logger.info(f"✅ Using audio file: {test_audio}")
    
    # Initialize agent
    logger.info("\nInitializing Transcriber Agent...")
    agent = get_transcriber_agent()
    logger.info("✅ Agent ready")
    
    # Test transcription
    logger.info("\nTesting transcription...")
    
    try:
        result = agent.transcribe_audio(
            audio_path=test_audio,
            meeting_context={
                "title": "Test Meeting",
                "description": "Testing transcription pipeline",
                "participants": ["Alice", "Bob"]
            }
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("TRANSCRIPTION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Duration: {result['duration']:.1f}s")
        logger.info(f"Processing time: {result['processing_time']:.1f}s")
        logger.info(f"Word count: {result['word_count']}")
        logger.info(f"Model: {result['model']}")
        logger.info(f"Language: {result['language']}")
        logger.info("\nRaw Transcript:")
        logger.info("-" * 60)
        logger.info(result['raw_transcript'][:500] + "..." if len(result['raw_transcript']) > 500 else result['raw_transcript'])
        logger.info("\nCleaned Transcript:")
        logger.info("-" * 60)
        logger.info(result['cleaned_transcript'][:500] + "..." if len(result['cleaned_transcript']) > 500 else result['cleaned_transcript'])
        logger.info("=" * 60)
        logger.info("✅ TRANSCRIPTION TEST PASSED!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    test_transcription()