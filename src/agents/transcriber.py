# # src/agents/transcriber.py
# """
# Transcriber Agent
# =================
# CrewAI agent that handles transcription and transcript cleaning

# Pipeline:
# 1. Whisper generates raw transcript (with um, uh, repetitions)
# 2. LLM agent cleans it up professionally
# 3. Output: Clean, formatted transcript ready for analysis
# """

# from crewai import Agent, Task, Crew, Process
# from groq import Groq
# from src.config import get_settings
# from src.core.transcription import get_transcription_service
# from src.core.audio_processor import get_audio_processor
# from src.monitoring.metrics import track_transcription_time, track_llm_call
# from typing import Dict, Optional
# import logging
# import time

# logger = logging.getLogger(__name__)
# settings = get_settings()

# class TranscriberAgent:
#     """
#     AI Agent for audio transcription and cleaning
    
#     Responsibilities:
#     - Convert audio to text (Whisper)
#     - Clean up transcript (remove filler words)
#     - Format for readability (paragraphs, structure)
#     - Preserve important context
#     """
    
#     def __init__(self):
#         """Initialize agent with Groq LLM"""
    
#         # Initialize Groq client
#         self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
    
#         # Create a ChatGroq instance for CrewAI
#         from langchain_groq import ChatGroq
    
#         llm = ChatGroq(
#             model="llama-3.1-70b-versatile",
#             api_key=settings.GROQ_API_KEY,
#             temperature=0.1
#         )
    
#         # Agent configuration with explicit LLM
#         self.agent = Agent(
#             role="Professional Meeting Transcriptionist",
#             goal="Convert audio recordings into clean, professional transcripts that are easy to read and understand",
#             backstory="""You are an expert transcriptionist with 10+ years of experience 
#             documenting corporate meetings. You excel at:
            
#             - Removing filler words (um, uh, like, you know) while keeping natural speech flow
#             - Fixing grammatical errors without changing meaning
#             - Breaking content into logical paragraphs when topics change
#             - Preserving technical terms and important context
#             - Creating professional documentation from conversational speech
            
#             You never add information that wasn't said. You never summarize or skip content.
#             Your goal is to make the transcript clear and professional while staying 100% accurate.""",
#             llm=llm,  # ← This is the fix! Explicitly provide the LLM
#             verbose=False,
#             allow_delegation=False
#         )
    
#         logger.info("✅ Transcriber Agent initialized with Groq LLM")
    
#     def transcribe_audio(
#         self,
#         audio_path: str,
#         meeting_context: Optional[Dict] = None,
#         optimize_audio: bool = True
#     ) -> Dict:
#         """
#         Main transcription pipeline
        
#         Args:
#             audio_path: Path to audio file
#             meeting_context: Optional context (title, participants, description)
#             optimize_audio: Convert to Whisper-optimized format
        
#         Returns:
#             {
#                 "raw_transcript": "...",
#                 "cleaned_transcript": "...",
#                 "segments": [...],
#                 "duration": 123.45,
#                 "word_count": 450,
#                 "processing_time": 45.2,
#                 "audio_info": {...}
#             }
#         """
#         logger.info(f"=" * 50)
#         logger.info(f"🎙️ Starting transcription pipeline")
#         logger.info(f"   Audio: {audio_path}")
#         logger.info(f"=" * 50)
        
#         pipeline_start = time.time()
        
#         try:
#             # Step 1: Validate and optimize audio
#             logger.info("Step 1: Validating audio...")
#             audio_processor = get_audio_processor()
            
#             is_valid, message = audio_processor.validate_audio_file(audio_path)
#             if not is_valid:
#                 raise ValueError(f"Invalid audio file: {message}")
            
#             audio_info = audio_processor.get_audio_info(audio_path)
#             logger.info(f"   ✅ Valid: {audio_info['duration']:.1f}s, {audio_info['format']}")
            
#             # Optimize for Whisper if requested
#             if optimize_audio:
#                 logger.info("Step 2: Optimizing audio for Whisper...")
#                 audio_path = audio_processor.convert_to_wav(audio_path)
#                 logger.info(f"   ✅ Optimized: 16kHz, mono")
            
#             # Step 2: Transcribe with Whisper
#             logger.info("Step 3: Transcribing with Whisper...")
#             transcription_service = get_transcription_service()
            
#             transcribe_start = time.time()
#             whisper_result = transcription_service.transcribe(audio_path)
#             transcribe_time = time.time() - transcribe_start
            
#             track_transcription_time(transcribe_time)
            
#             raw_transcript = whisper_result["text"]
#             segments = whisper_result["segments"]
            
#             logger.info(f"   ✅ Whisper done: {len(raw_transcript)} chars in {transcribe_time:.1f}s")
            
#             # Step 3: Clean with LLM
#             logger.info("Step 4: Cleaning transcript with LLM...")
#             clean_start = time.time()
            
#             cleaned_transcript = self._clean_transcript_with_llm(
#                 raw_transcript,
#                 meeting_context
#             )
            
#             clean_time = time.time() - clean_start
#             logger.info(f"   ✅ LLM cleaning done in {clean_time:.1f}s")
            
#             # Step 4: Calculate metrics
#             word_count = len(cleaned_transcript.split())
#             total_time = time.time() - pipeline_start
            
#             result = {
#                 "raw_transcript": raw_transcript,
#                 "cleaned_transcript": cleaned_transcript,
#                 "segments": segments,
#                 "duration": whisper_result["duration"],
#                 "word_count": word_count,
#                 "processing_time": total_time,
#                 "transcription_time": transcribe_time,
#                 "cleaning_time": clean_time,
#                 "audio_info": audio_info,
#                 "model": whisper_result["model"],
#                 "language": whisper_result["language"]
#             }
            
#             logger.info("=" * 50)
#             logger.info(f"✅ Transcription pipeline complete!")
#             logger.info(f"   Duration: {result['duration']:.1f}s")
#             logger.info(f"   Words: {word_count}")
#             logger.info(f"   Processing: {total_time:.1f}s")
#             logger.info("=" * 50)
            
#             return result
            
#         except Exception as e:
#             logger.error(f"❌ Transcription pipeline failed: {e}", exc_info=True)
#             raise
    
#     def _clean_transcript_with_llm(
#         self,
#         raw_transcript: str,
#         context: Optional[Dict] = None
#     ) -> str:
#         """
#         Use LLM to clean and format transcript
        
#         This is where the AI makes the transcript professional:
#         - Removes excessive filler words
#         - Fixes grammar
#         - Adds paragraph breaks
#         - Improves readability
#         """
        
#         # Build context string
#         context_str = ""
#         if context:
#             if context.get('title'):
#                 context_str += f"\nMeeting Title: {context['title']}"
#             if context.get('description'):
#                 context_str += f"\nDescription: {context['description']}"
#             if context.get('participants'):
#                 participants = ", ".join(context['participants'])
#                 context_str += f"\nParticipants: {participants}"
        
#         # Create prompt
#         prompt = f"""You are a professional transcriptionist. Clean up this meeting transcript.

# {context_str}

# RAW TRANSCRIPT:
# {raw_transcript}

# INSTRUCTIONS:
# 1. Remove excessive filler words (um, uh, like, you know) - but keep some for natural flow
# 2. Fix obvious grammatical errors
# 3. Break into paragraphs when the topic or speaker changes
# 4. Preserve ALL important information - don't skip anything
# 5. Keep technical terms, numbers, and names exactly as said
# 6. Do NOT summarize - keep the full content
# 7. Do NOT add information that wasn't said
# 8. Format professionally for business documentation

# OUTPUT FORMAT:
# Return ONLY the cleaned transcript. No explanations, no preamble, just the transcript."""

#         try:
#             # Call Groq API
#             logger.info("   Calling Groq API...")
            
#             response = self.groq_client.chat.completions.create(
#                 model="llama-3.1-70b-versatile",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "You are a professional transcriptionist. You clean transcripts while preserving all information."
#                     },
#                     {
#                         "role": "user",
#                         "content": prompt
#                     }
#                 ],
#                 temperature=0.1,  # Low temperature for consistency
#                 max_tokens=4000,
#                 top_p=0.95
#             )
            
#             cleaned = response.choices[0].message.content.strip()
            
#             # Track metrics
#             tokens_used = response.usage.total_tokens
#             track_llm_call(
#                 model="llama-3.1-70b",
#                 provider="groq",
#                 tokens=tokens_used
#             )
            
#             logger.info(f"   ✅ LLM cleaned: {len(cleaned)} chars, {tokens_used} tokens")
            
#             return cleaned
            
#         except Exception as e:
#             logger.error(f"   ❌ LLM cleaning failed: {e}")
#             logger.warning("   ⚠️  Falling back to raw transcript")
#             # Fallback: return raw transcript if LLM fails
#             return raw_transcript

# # ============================================
# # SINGLETON
# # ============================================

# _transcriber_agent: Optional[TranscriberAgent] = None

# def get_transcriber_agent() -> TranscriberAgent:
#     """Get transcriber agent (singleton)"""
#     global _transcriber_agent
#     if _transcriber_agent is None:
#         _transcriber_agent = TranscriberAgent()
#     return _transcriber_agent

# src/agents/transcriber.py
"""
Transcriber Agent (Simplified)
===============================
Direct Groq integration for transcript cleaning

Pipeline:
1. Whisper generates raw transcript (with um, uh, repetitions)
2. Groq LLM cleans it up professionally
3. Output: Clean, formatted transcript ready for analysis
"""

from groq import Groq
from src.config import get_settings
from src.core.transcription import get_transcription_service
from src.core.audio_processor import get_audio_processor
from src.monitoring.metrics import track_transcription_time, track_llm_call
from typing import Dict, Optional
import logging
import time

logger = logging.getLogger(__name__)
settings = get_settings()

class TranscriberAgent:
    """
    AI Agent for audio transcription and cleaning
    
    Responsibilities:
    - Convert audio to text (Whisper)
    - Clean up transcript (remove filler words)
    - Format for readability (paragraphs, structure)
    - Preserve important context
    """
    
    def __init__(self):
        """Initialize agent with Groq LLM"""
        
        # Initialize Groq client
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        
        logger.info("✅ Transcriber Agent initialized with Groq")
    
    def transcribe_audio(
        self,
        audio_path: str,
        meeting_context: Optional[Dict] = None,
        optimize_audio: bool = True
    ) -> Dict:
        """
        Main transcription pipeline
        
        Args:
            audio_path: Path to audio file
            meeting_context: Optional context (title, participants, description)
            optimize_audio: Convert to Whisper-optimized format
        
        Returns:
            {
                "raw_transcript": "...",
                "cleaned_transcript": "...",
                "segments": [...],
                "duration": 123.45,
                "word_count": 450,
                "processing_time": 45.2,
                "audio_info": {...}
            }
        """
        logger.info(f"=" * 50)
        logger.info(f"🎙️ Starting transcription pipeline")
        logger.info(f"   Audio: {audio_path}")
        logger.info(f"=" * 50)
        
        pipeline_start = time.time()
        
        try:
            # Step 1: Validate and optimize audio
            logger.info("Step 1: Validating audio...")
            audio_processor = get_audio_processor()
            
            is_valid, message = audio_processor.validate_audio_file(audio_path)
            if not is_valid:
                raise ValueError(f"Invalid audio file: {message}")
            
            audio_info = audio_processor.get_audio_info(audio_path)
            logger.info(f"   ✅ Valid: {audio_info['duration']:.1f}s, {audio_info['format']}")
            
            # Optimize for Whisper if requested
            if optimize_audio:
                logger.info("Step 2: Optimizing audio for Whisper...")
                audio_path = audio_processor.convert_to_wav(audio_path)
                logger.info(f"   ✅ Optimized: 16kHz, mono")
            
            # Step 2: Transcribe with Whisper
            logger.info("Step 3: Transcribing with Whisper...")
            transcription_service = get_transcription_service()
            
            transcribe_start = time.time()
            whisper_result = transcription_service.transcribe(audio_path)
            transcribe_time = time.time() - transcribe_start
            
            track_transcription_time(transcribe_time)
            
            raw_transcript = whisper_result["text"]
            segments = whisper_result["segments"]
            
            logger.info(f"   ✅ Whisper done: {len(raw_transcript)} chars in {transcribe_time:.1f}s")
            
            # Step 3: Clean with LLM
            logger.info("Step 4: Cleaning transcript with LLM...")
            clean_start = time.time()
            
            cleaned_transcript = self._clean_transcript_with_llm(
                raw_transcript,
                meeting_context
            )
            
            clean_time = time.time() - clean_start
            logger.info(f"   ✅ LLM cleaning done in {clean_time:.1f}s")
            
            # Step 4: Calculate metrics
            word_count = len(cleaned_transcript.split())
            total_time = time.time() - pipeline_start
            
            result = {
                "raw_transcript": raw_transcript,
                "cleaned_transcript": cleaned_transcript,
                "segments": segments,
                "duration": whisper_result["duration"],
                "word_count": word_count,
                "processing_time": total_time,
                "transcription_time": transcribe_time,
                "cleaning_time": clean_time,
                "audio_info": audio_info,
                "model": whisper_result["model"],
                "language": whisper_result["language"]
            }
            
            logger.info("=" * 50)
            logger.info(f"✅ Transcription pipeline complete!")
            logger.info(f"   Duration: {result['duration']:.1f}s")
            logger.info(f"   Words: {word_count}")
            logger.info(f"   Processing: {total_time:.1f}s")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Transcription pipeline failed: {e}", exc_info=True)
            raise
    
    def _clean_transcript_with_llm(
        self,
        raw_transcript: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Use LLM to clean and format transcript
        
        This is where the AI makes the transcript professional:
        - Removes excessive filler words
        - Fixes grammar
        - Adds paragraph breaks
        - Improves readability
        """
        
        # Build context string
        context_str = ""
        if context:
            if context.get('title'):
                context_str += f"\nMeeting Title: {context['title']}"
            if context.get('description'):
                context_str += f"\nDescription: {context['description']}"
            if context.get('participants'):
                participants = ", ".join(context['participants'])
                context_str += f"\nParticipants: {participants}"
        
        # Create prompt
        prompt = f"""You are a professional transcriptionist. Clean up this meeting transcript.

{context_str}

RAW TRANSCRIPT:
{raw_transcript}

INSTRUCTIONS:
1. Remove excessive filler words (um, uh, like, you know) - but keep some for natural flow
2. Fix obvious grammatical errors
3. Break into paragraphs when the topic or speaker changes
4. Preserve ALL important information - don't skip anything
5. Keep technical terms, numbers, and names exactly as said
6. Do NOT summarize - keep the full content
7. Do NOT add information that wasn't said
8. Format professionally for business documentation

OUTPUT FORMAT:
Return ONLY the cleaned transcript. No explanations, no preamble, just the transcript."""

        try:
            # Call Groq API
            logger.info("   Calling Groq API for transcript cleaning...")
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional transcriptionist. You clean transcripts while preserving all information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=4000,
                top_p=0.95
            )
            
            cleaned = response.choices[0].message.content.strip()
            
            # Track metrics
            tokens_used = response.usage.total_tokens
            track_llm_call(
                model="llama-3.1-70b",
                provider="groq",
                tokens=tokens_used
            )
            
            logger.info(f"   ✅ LLM cleaned: {len(cleaned)} chars, {tokens_used} tokens")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"   ❌ LLM cleaning failed: {e}")
            logger.warning("   ⚠️  Falling back to raw transcript")
            # Fallback: return raw transcript if LLM fails
            return raw_transcript

# ============================================
# SINGLETON
# ============================================

_transcriber_agent: Optional[TranscriberAgent] = None

def get_transcriber_agent() -> TranscriberAgent:
    """Get transcriber agent (singleton)"""
    global _transcriber_agent
    if _transcriber_agent is None:
        _transcriber_agent = TranscriberAgent()
    return _transcriber_agent