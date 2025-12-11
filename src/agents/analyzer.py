# src/agents/analyzer.py
"""
Content Analyzer Agent
======================
Analyzes meeting content to extract insights

Extracts:
- Key topics discussed
- Sentiment analysis
- Important decisions made
- Questions raised
- Participant involvement
"""

from groq import Groq
from src.config import get_settings
from src.monitoring.metrics import track_llm_call
from typing import Dict, List, Optional
import logging
import json

logger = logging.getLogger(__name__)
settings = get_settings()

class ContentAnalyzerAgent:
    """
    Agent for analyzing meeting content
    
    Responsibilities:
    - Extract main topics discussed
    - Analyze overall sentiment
    - Identify key decisions
    - Find questions and concerns
    - Track participant engagement
    """
    
    def __init__(self):
        """Initialize analyzer agent"""
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("✅ Content Analyzer Agent initialized")
    
    def analyze(self, transcript: str, meeting_context: Optional[Dict] = None) -> Dict:
        """
        Analyze meeting transcript
        
        Args:
            transcript: Meeting transcript text
            meeting_context: Optional meeting metadata
        
        Returns:
            {
                "key_topics": ["topic1", "topic2", ...],
                "sentiment": {
                    "overall_score": 0.7,  # -1 to 1
                    "summary": "Positive and productive"
                },
                "decisions": ["decision1", "decision2"],
                "questions": ["question1", "question2"],
                "concerns": ["concern1"],
                "highlights": ["important point 1", ...]
            }
        """
        logger.info("🔍 Starting content analysis...")
        
        # Build context
        context_str = ""
        if meeting_context:
            if meeting_context.get('title'):
                context_str += f"\nMeeting: {meeting_context['title']}"
            if meeting_context.get('participants'):
                context_str += f"\nParticipants: {', '.join(meeting_context['participants'])}"
        
        prompt = f"""You are an expert meeting analyst. Analyze this meeting transcript and extract key insights.

{context_str}

TRANSCRIPT:
{transcript}

Analyze and return a JSON object with:
1. key_topics: List of 3-7 main topics discussed (short phrases)
2. sentiment: Object with:
   - overall_score: Number from -1 (very negative) to 1 (very positive)
   - summary: Brief explanation of the sentiment
3. decisions: List of key decisions made (if any)
4. questions: Important questions raised that need answers
5. concerns: Any concerns or issues mentioned
6. highlights: 3-5 most important points from the meeting

Return ONLY valid JSON, no markdown, no explanation.

Example format:
{{
  "key_topics": ["Q4 budget", "hiring plan", "product launch"],
  "sentiment": {{
    "overall_score": 0.6,
    "summary": "Generally positive with some concerns about timeline"
  }},
  "decisions": ["Approved Q4 budget of $500K", "Start hiring 2 engineers"],
  "questions": ["When will the vendor respond?"],
  "concerns": ["Timeline might be too aggressive"],
  "highlights": ["Budget approved", "Hiring authorized", "Product on track"]
}}"""

        try:
            logger.info("   Calling Groq API for content analysis...")
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert meeting analyst. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            # Parse JSON
            analysis = json.loads(result_text)
            
            # Track metrics
            tokens_used = response.usage.total_tokens
            track_llm_call(
                model="llama-3.3-70b",
                provider="groq",
                tokens=tokens_used
            )
            
            logger.info(f"   ✅ Analysis complete: {len(analysis.get('key_topics', []))} topics, {tokens_used} tokens")
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"   ❌ Failed to parse JSON response: {e}")
            logger.error(f"   Raw response: {result_text[:500]}")
            
            # Return fallback
            return {
                "key_topics": [],
                "sentiment": {"overall_score": 0.0, "summary": "Unable to analyze"},
                "decisions": [],
                "questions": [],
                "concerns": [],
                "highlights": []
            }
        
        except Exception as e:
            logger.error(f"   ❌ Content analysis failed: {e}")
            return {
                "key_topics": [],
                "sentiment": {"overall_score": 0.0, "summary": "Analysis failed"},
                "decisions": [],
                "questions": [],
                "concerns": [],
                "highlights": []
            }

# Singleton
_content_analyzer_agent: Optional[ContentAnalyzerAgent] = None

def get_content_analyzer_agent() -> ContentAnalyzerAgent:
    """Get content analyzer agent (singleton)"""
    global _content_analyzer_agent
    if _content_analyzer_agent is None:
        _content_analyzer_agent = ContentAnalyzerAgent()
    return _content_analyzer_agent