# src/agents/summarizer.py
"""
Summarizer Agent
================
Generates meeting summaries at different detail levels

Summary Types:
1. Executive Summary (2-3 sentences) - For busy executives
2. Standard Summary (1 paragraph) - For team members
3. Detailed Summary (multiple paragraphs) - For documentation
"""

from groq import Groq
from src.config import get_settings
from src.monitoring.metrics import track_llm_call
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class SummarizerAgent:
    """
    Agent for generating meeting summaries
    
    Creates summaries that:
    - Capture main points
    - Include key decisions
    - Mention action items
    - Preserve important context
    """
    
    def __init__(self):
        """Initialize summarizer agent"""
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("✅ Summarizer Agent initialized")
    
    def generate_summary(
        self,
        transcript: str,
        meeting_context: Optional[Dict] = None,
        summary_type: str = "standard"
    ) -> str:
        """
        Generate meeting summary
        
        Args:
            transcript: Meeting transcript
            meeting_context: Optional meeting metadata
            summary_type: "executive", "standard", or "detailed"
        
        Returns:
            Summary text
        """
        logger.info(f"📝 Generating {summary_type} summary...")
        
        # Build context
        context_str = ""
        if meeting_context:
            if meeting_context.get('title'):
                context_str += f"\nMeeting: {meeting_context['title']}"
            if meeting_context.get('description'):
                context_str += f"\nPurpose: {meeting_context['description']}"
            if meeting_context.get('participants'):
                context_str += f"\nParticipants: {', '.join(meeting_context['participants'])}"
        
        # Different prompts for different summary types
        prompts = {
            "executive": """Create an EXECUTIVE SUMMARY (2-3 sentences maximum).

Focus on:
- What was decided
- What are the next steps
- Any urgent matters

Keep it brief and actionable.""",
            
            "standard": """Create a STANDARD SUMMARY (1-2 paragraphs).

Include:
- Main topics discussed
- Key decisions made
- Important action items
- Any concerns or blockers

Keep it concise but informative.""",
            
            "detailed": """Create a DETAILED SUMMARY (3-4 paragraphs).

Include:
- Context and background
- All topics discussed in order
- Detailed decisions and rationale
- All action items with owners
- Questions raised and concerns
- Next steps and follow-ups

Be thorough but organized."""
        }
        
        prompt_type = prompts.get(summary_type, prompts["standard"])
        
        prompt = f"""You are an expert at summarizing meetings.

{context_str}

TRANSCRIPT:
{transcript}

{prompt_type}

Write in professional business language. Use past tense. Be objective.
Return ONLY the summary text, no title, no preamble."""

        try:
            logger.info(f"   Calling Groq API for {summary_type} summary...")
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert meeting summarizer. You create clear, concise summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Track metrics
            tokens_used = response.usage.total_tokens
            track_llm_call(
                model="llama-3.3-70b",
                provider="groq",
                tokens=tokens_used
            )
            
            logger.info(f"   ✅ Summary generated: {len(summary)} chars, {tokens_used} tokens")
            
            return summary
            
        except Exception as e:
            logger.error(f"   ❌ Summary generation failed: {e}")
            return "Summary generation failed."
    
    def generate_all_summaries(
        self,
        transcript: str,
        meeting_context: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate all three summary types
        
        Returns:
            {
                "executive": "...",
                "standard": "...",
                "detailed": "..."
            }
        """
        return {
            "executive": self.generate_summary(transcript, meeting_context, "executive"),
            "standard": self.generate_summary(transcript, meeting_context, "standard"),
            "detailed": self.generate_summary(transcript, meeting_context, "detailed")
        }

# Singleton
_summarizer_agent: Optional[SummarizerAgent] = None

def get_summarizer_agent() -> SummarizerAgent:
    """Get summarizer agent (singleton)"""
    global _summarizer_agent
    if _summarizer_agent is None:
        _summarizer_agent = SummarizerAgent()
    return _summarizer_agent