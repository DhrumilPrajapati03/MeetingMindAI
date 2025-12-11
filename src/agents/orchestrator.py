# src/agents/orchestrator.py
"""
Agent Orchestrator
==================
Coordinates all AI agents to process meetings

Pipeline:
1. Transcriber → Clean transcript
2. Content Analyzer → Extract insights
3. Action Hunter → Find tasks
4. Summarizer → Generate summary

All results saved to database
"""

from src.agents.transcriber import get_transcriber_agent
from src.agents.analyzer import get_content_analyzer_agent
from src.agents.action_hunter import get_action_hunter_agent
from src.agents.summarizer import get_summarizer_agent
from typing import Dict, Optional
import logging
import time

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Orchestrates all AI agents to fully process a meeting
    
    Workflow:
    Audio → Transcription → Analysis → Action Items → Summary → Database
    """
    
    def __init__(self):
        """Initialize orchestrator with all agents"""
        self.transcriber = get_transcriber_agent()
        self.analyzer = get_content_analyzer_agent()
        self.action_hunter = get_action_hunter_agent()
        self.summarizer = get_summarizer_agent()
        
        logger.info("✅ Agent Orchestrator initialized with 4 agents")
    
    def process_meeting_full(
        self,
        audio_path: str,
        meeting_context: Optional[Dict] = None
    ) -> Dict:
        """
        Full meeting processing pipeline
        
        Args:
            audio_path: Path to audio file
            meeting_context: Meeting metadata
        
        Returns:
            Complete processing results including:
            - Transcript (raw + cleaned)
            - Analysis (topics, sentiment, decisions)
            - Action items
            - Summary
            - Processing metrics
        """
        logger.info("=" * 70)
        logger.info("🎬 FULL MEETING PROCESSING PIPELINE")
        logger.info("=" * 70)
        
        pipeline_start = time.time()
        results = {}
        
        try:
            # Step 1: Transcription
            logger.info("\n📍 Step 1/4: Transcription")
            transcription_result = self.transcriber.transcribe_audio(
                audio_path,
                meeting_context
            )
            
            results['transcription'] = transcription_result
            cleaned_transcript = transcription_result['cleaned_transcript']
            
            # Step 2: Content Analysis
            logger.info("\n📍 Step 2/4: Content Analysis")
            analysis_result = self.analyzer.analyze(
                cleaned_transcript,
                meeting_context
            )
            
            results['analysis'] = analysis_result
            
            # Step 3: Action Item Extraction
            logger.info("\n📍 Step 3/4: Action Item Extraction")
            action_items = self.action_hunter.extract_action_items(
                cleaned_transcript,
                meeting_context
            )
            
            results['action_items'] = action_items
            
            # Step 4: Summary Generation
            logger.info("\n📍 Step 4/4: Summary Generation")
            summary = self.summarizer.generate_summary(
                cleaned_transcript,
                meeting_context,
                summary_type="standard"
            )
            
            results['summary'] = summary
            
            # Calculate totals
            total_time = time.time() - pipeline_start
            
            results['metadata'] = {
                'total_processing_time': total_time,
                'duration': transcription_result['duration'],
                'word_count': transcription_result['word_count'],
                'action_item_count': len(action_items),
                'topic_count': len(analysis_result.get('key_topics', []))
            }
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ PIPELINE COMPLETE!")
            logger.info(f"   Total time: {total_time:.1f}s")
            logger.info(f"   Words: {transcription_result['word_count']}")
            logger.info(f"   Topics: {len(analysis_result.get('key_topics', []))}")
            logger.info(f"   Action items: {len(action_items)}")
            logger.info("=" * 70)
            
            return results
            
        except Exception as e:
            logger.error(f"\n❌ Pipeline failed: {e}", exc_info=True)
            raise

# Singleton
_orchestrator: Optional[AgentOrchestrator] = None

def get_orchestrator() -> AgentOrchestrator:
    """Get agent orchestrator (singleton)"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator