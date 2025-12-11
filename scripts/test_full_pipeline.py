# scripts/test_full_pipeline.py
"""
Test Complete AI Pipeline
==========================
Tests all agents working together
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.orchestrator import get_orchestrator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_pipeline():
    """Test the complete AI agent pipeline"""
    
    logger.info("=" * 70)
    logger.info("TESTING COMPLETE AI PIPELINE")
    logger.info("=" * 70)
    
    # Audio file
    audio_file = "data/uploads/videoplayback.m4a"
    
    if not Path(audio_file).exists():
        logger.error(f"❌ Audio file not found: {audio_file}")
        logger.info("Please place an audio file at: data/uploads/videoplayback.m4a")
        return
    
    # Meeting context
    context = {
        "title": "Q4 Planning Meeting",
        "description": "Quarterly planning and budget discussion",
        "participants": ["Alice", "Bob", "Charlie"]
    }
    
    # Run full pipeline
    logger.info(f"\n🎬 Processing: {audio_file}")
    logger.info(f"   Context: {context['title']}")
    
    try:
        orchestrator = get_orchestrator()
        results = orchestrator.process_meeting_full(audio_file, context)
        
        # Display results
        logger.info("\n" + "=" * 70)
        logger.info("📊 RESULTS")
        logger.info("=" * 70)
        
        # Transcription
        logger.info(f"\n📝 TRANSCRIPT ({results['transcription']['word_count']} words):")
        logger.info("-" * 70)
        transcript = results['transcription']['cleaned_transcript']
        logger.info(transcript[:500] + "..." if len(transcript) > 500 else transcript)
        
        # Analysis
        logger.info(f"\n🔍 CONTENT ANALYSIS:")
        logger.info("-" * 70)
        analysis = results['analysis']
        logger.info(f"   Topics: {', '.join(analysis.get('key_topics', []))}")
        logger.info(f"   Sentiment: {analysis.get('sentiment', {}).get('overall_score', 0):.2f}")
        logger.info(f"   Summary: {analysis.get('sentiment', {}).get('summary', 'N/A')}")
        
        if analysis.get('decisions'):
            logger.info(f"   Decisions: {len(analysis['decisions'])}")
            for i, decision in enumerate(analysis['decisions'][:3], 1):
                logger.info(f"      {i}. {decision}")
        
        # Action Items
        logger.info(f"\n💼 ACTION ITEMS ({len(results['action_items'])}):")
        logger.info("-" * 70)
        for i, item in enumerate(results['action_items'], 1):
            logger.info(f"   {i}. {item['title']}")
            logger.info(f"      → Assigned: {item.get('assigned_to', 'Unassigned')}")
            logger.info(f"      → Priority: {item.get('priority', 'medium')}")
            logger.info(f"      → Due: {item.get('due_date', 'Not specified')}")
            logger.info(f"      → Confidence: {item.get('confidence', 0):.0%}")
        
        # Summary
        logger.info(f"\n📋 SUMMARY:")
        logger.info("-" * 70)
        logger.info(results['summary'])
        
        # Metrics
        logger.info(f"\n⏱️  PROCESSING METRICS:")
        logger.info("-" * 70)
        metadata = results['metadata']
        logger.info(f"   Total time: {metadata['total_processing_time']:.1f}s")
        logger.info(f"   Audio duration: {metadata['duration']:.1f}s")
        logger.info(f"   RTF: {metadata['total_processing_time']/metadata['duration']:.2f}x")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ PIPELINE TEST PASSED!")
        logger.info("=" * 70)
        
        # Save results
        output_file = Path("data/processed/full_pipeline_result.txt")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("FULL PIPELINE RESULTS\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Meeting: {context['title']}\n")
            f.write(f"Participants: {', '.join(context['participants'])}\n\n")
            f.write(f"TRANSCRIPT:\n{'-' * 70}\n")
            f.write(results['transcription']['cleaned_transcript'] + "\n\n")
            f.write(f"SUMMARY:\n{'-' * 70}\n")
            f.write(results['summary'] + "\n\n")
            f.write(f"TOPICS:\n{'-' * 70}\n")
            for topic in analysis.get('key_topics', []):
                f.write(f"- {topic}\n")
            f.write(f"\nACTION ITEMS:\n{'-' * 70}\n")
            for i, item in enumerate(results['action_items'], 1):
                f.write(f"{i}. {item['title']}\n")
                f.write(f"   Assigned: {item.get('assigned_to')}\n")
                f.write(f"   Priority: {item.get('priority')}\n")
                f.write(f"   Due: {item.get('due_date', 'Not specified')}\n\n")
        
        logger.info(f"\n💾 Full results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    test_full_pipeline()