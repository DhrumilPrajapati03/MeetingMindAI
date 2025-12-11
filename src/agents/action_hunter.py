# src/agents/action_hunter.py
"""
Action Item Hunter Agent
========================
Extracts action items from meeting transcripts

Action Item = Task + Assignee + Deadline (optional)

Example:
"Alice, can you send the report by Friday?"
→ Action: "Send report"
→ Assigned to: Alice
→ Due: Friday (this week)
→ Priority: Medium
"""

from groq import Groq
from src.config import get_settings
from src.monitoring.metrics import track_llm_call, track_action_items
from typing import Dict, List, Optional
import logging
import json
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)
settings = get_settings()

class ActionItemHunterAgent:
    """
    Agent for extracting action items from meetings
    
    Looks for:
    - Explicit tasks ("Alice, please do X")
    - Commitments ("I'll handle Y")
    - Deadlines ("by Friday", "next week")
    - Priorities (urgent, important, etc.)
    """
    
    def __init__(self):
        """Initialize action hunter agent"""
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("✅ Action Item Hunter Agent initialized")
    
    def extract_action_items(
        self,
        transcript: str,
        meeting_context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Extract action items from transcript
        
        Args:
            transcript: Meeting transcript
            meeting_context: Optional meeting metadata
        
        Returns:
            List of action items:
            [
                {
                    "title": "Send budget report",
                    "description": "Prepare and send Q4 budget analysis",
                    "assigned_to": "Alice",
                    "due_date": "2024-12-15",
                    "priority": "high",
                    "confidence": 0.95,
                    "snippet": "Alice, can you send the budget report by Friday?"
                },
                ...
            ]
        """
        logger.info("🎯 Extracting action items...")
        
        # Build context
        context_str = ""
        if meeting_context:
            if meeting_context.get('title'):
                context_str += f"\nMeeting: {meeting_context['title']}"
            if meeting_context.get('participants'):
                participants = ', '.join(meeting_context['participants'])
                context_str += f"\nParticipants: {participants}"
            if meeting_context.get('meeting_date'):
                context_str += f"\nMeeting Date: {meeting_context['meeting_date']}"
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""You are an expert at identifying action items from meeting transcripts.

{context_str}
Today's Date: {today}

TRANSCRIPT:
{transcript}

Extract ALL action items. An action item is:
- A task someone needs to complete
- A commitment someone made
- A follow-up that was requested

For each action item, provide:
1. title: Brief task description (max 100 chars)
2. description: More detailed explanation (optional)
3. assigned_to: Person's name (or "Unassigned" if unclear)
4. due_date: Deadline in YYYY-MM-DD format (or null if not mentioned)
   - "by Friday" → calculate next Friday
   - "next week" → 7 days from today
   - "by end of month" → last day of current month
5. priority: "low", "medium", "high", or "critical"
6. confidence: 0.0 to 1.0 (how confident you are this is an action item)
7. snippet: Exact quote from transcript where this was mentioned

Return ONLY valid JSON array, no markdown, no explanation.

Example:
[
  {{
    "title": "Send budget report",
    "description": "Prepare and send Q4 budget analysis to finance team",
    "assigned_to": "Alice",
    "due_date": "2024-12-13",
    "priority": "high",
    "confidence": 0.95,
    "snippet": "Alice, can you send the budget report by Friday?"
  }},
  {{
    "title": "Schedule follow-up meeting",
    "description": "Coordinate with stakeholders for next discussion",
    "assigned_to": "Bob",
    "due_date": null,
    "priority": "medium",
    "confidence": 0.85,
    "snippet": "Bob mentioned he'll schedule a follow-up."
  }}
]

If no action items found, return empty array: []"""

        try:
            logger.info("   Calling Groq API for action item extraction...")
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting action items from meetings. Always return valid JSON array."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Lower temperature for consistency
                max_tokens=3000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            # Parse JSON
            action_items = json.loads(result_text)
            
            # Validate and clean
            validated_items = []
            for item in action_items:
                # Ensure required fields
                if not item.get('title'):
                    continue
                
                # Clean and validate
                validated_item = {
                    "title": item['title'][:500],
                    "description": item.get('description', '')[:2000] if item.get('description') else None,
                    "assigned_to": item.get('assigned_to', 'Unassigned')[:255],
                    "due_date": self._parse_due_date(item.get('due_date')),
                    "priority": self._validate_priority(item.get('priority', 'medium')),
                    "confidence": float(item.get('confidence', 0.5)),
                    "snippet": item.get('snippet', '')[:1000] if item.get('snippet') else None
                }
                
                validated_items.append(validated_item)
            
            # Track metrics
            tokens_used = response.usage.total_tokens
            track_llm_call(
                model="llama-3.3-70b",
                provider="groq",
                tokens=tokens_used
            )
            track_action_items(len(validated_items))
            
            logger.info(f"   ✅ Extracted {len(validated_items)} action items, {tokens_used} tokens")
            
            return validated_items
            
        except json.JSONDecodeError as e:
            logger.error(f"   ❌ Failed to parse JSON: {e}")
            logger.error(f"   Raw response: {result_text[:500]}")
            return []
        
        except Exception as e:
            logger.error(f"   ❌ Action item extraction failed: {e}")
            return []
    
    def _parse_due_date(self, due_date: Optional[str]) -> Optional[str]:
        """Parse and validate due date"""
        if not due_date or due_date == "null":
            return None
        
        # If already in YYYY-MM-DD format, return as-is
        if re.match(r'^\d{4}-\d{2}-\d{2}$', due_date):
            return due_date
        
        # TODO: Add more date parsing logic if needed
        return None
    
    def _validate_priority(self, priority: str) -> str:
        """Validate priority value"""
        valid_priorities = ["low", "medium", "high", "critical"]
        priority_lower = priority.lower().strip()
        
        if priority_lower in valid_priorities:
            return priority_lower
        
        return "medium"  # Default

# Singleton
_action_hunter_agent: Optional[ActionItemHunterAgent] = None

def get_action_hunter_agent() -> ActionItemHunterAgent:
    """Get action hunter agent (singleton)"""
    global _action_hunter_agent
    if _action_hunter_agent is None:
        _action_hunter_agent = ActionItemHunterAgent()
    return _action_hunter_agent