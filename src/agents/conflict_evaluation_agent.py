"""
Conflict Evaluation Agent - Detects scheduling conflicts
Uses rule-based detection and AI-powered resolution suggestions
"""
import sys
import json
import requests
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schedule_item import ScheduleItem, EventType
from models.conflict import Conflict, ConflictType
from config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    OPENAI_DEPLOYMENT_NAME,
    OPENAI_API_VERSION
)


class ConflictEvaluationAgent:
    """
    Detects scheduling conflicts using rule-based and AI-powered analysis.
    
    Conflict Types:
    - TIME_OVERLAP: Two events at the same time
    - DOUBLE_BOOKING: Exact same time slot
    - BACK_TO_BACK: No travel time between different locations
    - LOCATION_CONFLICT: Same room booked twice
    """
    
    def __init__(self, existing_events: List[ScheduleItem] = None):
        self.existing_events = existing_events or []
        self.api_url = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={OPENAI_API_VERSION}"
        self.headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY
        }
    
    def set_events(self, events: List[ScheduleItem]):
        """Set the list of events to check for conflicts"""
        self.existing_events = events
    
    def check_conflicts(self, schedule: List[ScheduleItem] = None) -> List[Conflict]:
        """
        Check for all conflicts in the schedule.
        
        Args:
            schedule: List of events to check. Uses existing_events if not provided.
        
        Returns:
            List of Conflict objects describing each conflict found.
        """
        events = schedule or self.existing_events
        conflicts = []
        
        if not events:
            return conflicts
        
        # Sort by date and time
        sorted_schedule = sorted(events, key=lambda x: (x.date, x.start_time))
        
        # Check each pair of events
        for i in range(len(sorted_schedule)):
            for j in range(i + 1, len(sorted_schedule)):
                event_a = sorted_schedule[i]
                event_b = sorted_schedule[j]
                
                # Only check events on the same day
                if event_a.date != event_b.date:
                    continue
                
                conflict = self._check_pair_conflict(event_a, event_b)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _check_pair_conflict(self, event_a: ScheduleItem, event_b: ScheduleItem) -> Optional[Conflict]:
        """Check if two events conflict"""
        
        # Parse times
        try:
            a_start = datetime.strptime(f"{event_a.date} {event_a.start_time}", "%Y-%m-%d %H:%M")
            a_end = datetime.strptime(f"{event_a.date} {event_a.end_time}", "%Y-%m-%d %H:%M")
            b_start = datetime.strptime(f"{event_b.date} {event_b.start_time}", "%Y-%m-%d %H:%M")
            b_end = datetime.strptime(f"{event_b.date} {event_b.end_time}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            print(f"⚠️ Time parsing error: {e}")
            return None
        
        # Check for exact overlap (double booking)
        if a_start == b_start and a_end == b_end:
            return Conflict(
                conflict_type=ConflictType.DOUBLE_BOOKING,
                event_a=event_a,
                event_b=event_b,
                severity="high",
                message=f"Double booking: '{event_a.course}' and '{event_b.course}' are at exactly the same time ({event_a.start_time}-{event_a.end_time})"
            )
        
        # Check for time overlap
        if a_start < b_end and b_start < a_end:
            return Conflict(
                conflict_type=ConflictType.TIME_OVERLAP,
                event_a=event_a,
                event_b=event_b,
                severity="high",
                message=f"Time overlap: '{event_a.course}' ({event_a.start_time}-{event_a.end_time}) overlaps with '{event_b.course}' ({event_b.start_time}-{event_b.end_time})"
            )
        
        # Check for back-to-back with different locations (no travel time)
        if a_end == b_start and event_a.location and event_b.location:
            if event_a.location.lower() != event_b.location.lower():
                return Conflict(
                    conflict_type=ConflictType.BACK_TO_BACK,
                    event_a=event_a,
                    event_b=event_b,
                    severity="medium",
                    message=f"Back-to-back: '{event_a.course}' at {event_a.location} ends at {event_a.end_time} when '{event_b.course}' at {event_b.location} starts (no travel time)"
                )
        
        return None
    
    def check_new_event_conflicts(self, new_event: ScheduleItem, existing_schedule: List[ScheduleItem] = None) -> List[Conflict]:
        """
        Check if a new event conflicts with the existing schedule.
        
        Args:
            new_event: The event to check
            existing_schedule: Schedule to check against (uses self.existing_events if not provided)
        
        Returns:
            List of conflicts with the new event
        """
        schedule = existing_schedule or self.existing_events
        conflicts = []
        
        for existing in schedule:
            if existing.date == new_event.date:
                conflict = self._check_pair_conflict(new_event, existing)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def flag_conflicts(self, schedule: List[ScheduleItem] = None) -> str:
        """
        Check for conflicts and return a formatted status message.
        """
        conflicts = self.check_conflicts(schedule)
        
        if not conflicts:
            return "✅ No conflicts detected in the schedule"
        
        message = f"⚠️ Found {len(conflicts)} conflict(s):\n"
        for i, conflict in enumerate(conflicts, 1):
            severity_icon = "🔴" if conflict.severity == "high" else "🟡"
            message += f"\n{i}. {severity_icon} {conflict.message}"
        
        return message
    
    def get_ai_resolution(self, conflict: Conflict) -> str:
        """
        Use AI to suggest resolution for a conflict.
        
        Args:
            conflict: The conflict to resolve
        
        Returns:
            AI-generated resolution suggestion
        """
        messages = [
            {
                "role": "system",
                "content": """You are a scheduling assistant. Analyze the conflict and suggest practical resolutions.
Be concise and provide 2-3 specific actionable suggestions."""
            },
            {
                "role": "user",
                "content": f"""There's a scheduling conflict:

Conflict Type: {conflict.conflict_type.value}
Event A: {conflict.event_a.course} on {conflict.event_a.date} from {conflict.event_a.start_time} to {conflict.event_a.end_time} at {conflict.event_a.location}
Event B: {conflict.event_b.course} on {conflict.event_b.date} from {conflict.event_b.start_time} to {conflict.event_b.end_time} at {conflict.event_b.location}

Suggest how to resolve this conflict."""
            }
        ]
        
        try:
            payload = {
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 300
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Could not generate AI suggestion (Error {response.status_code})"
                
        except Exception as e:
            return f"Could not generate AI suggestion: {e}"
    
    def find_free_slots(self, schedule: List[ScheduleItem], date: str, duration_minutes: int = 60) -> List[Tuple[str, str]]:
        """
        Find free time slots on a given date.
        
        Args:
            schedule: Current schedule
            date: Date to search (YYYY-MM-DD)
            duration_minutes: Required slot duration
        
        Returns:
            List of (start_time, end_time) tuples for free slots
        """
        # Get events for the date
        day_events = [e for e in schedule if e.date == date]
        day_events.sort(key=lambda x: x.start_time)
        
        free_slots = []
        day_start = datetime.strptime(f"{date} 08:00", "%Y-%m-%d %H:%M")
        day_end = datetime.strptime(f"{date} 20:00", "%Y-%m-%d %H:%M")
        
        current_time = day_start
        
        for event in day_events:
            try:
                event_start = datetime.strptime(f"{date} {event.start_time}", "%Y-%m-%d %H:%M")
                event_end = datetime.strptime(f"{date} {event.end_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            
            # Check gap before this event
            gap = (event_start - current_time).total_seconds() / 60
            if gap >= duration_minutes:
                free_slots.append((
                    current_time.strftime("%H:%M"),
                    event_start.strftime("%H:%M")
                ))
            
            current_time = max(current_time, event_end)
        
        # Check time after last event
        remaining = (day_end - current_time).total_seconds() / 60
        if remaining >= duration_minutes:
            free_slots.append((
                current_time.strftime("%H:%M"),
                day_end.strftime("%H:%M")
            ))
        
        return free_slots
    
    def is_conflicting(self, event1: dict, event2: dict) -> bool:
        """
        Legacy method: Check if two events conflict (dict format).
        """
        if event1.get('date') != event2.get('date'):
            return False
        
        e1_start = event1.get('start_time', event1.get('from', '00:00'))
        e1_end = event1.get('end_time', event1.get('to', '23:59'))
        e2_start = event2.get('start_time', event2.get('from', '00:00'))
        e2_end = event2.get('end_time', event2.get('to', '23:59'))
        
        return not (e1_end <= e2_start or e2_end <= e1_start)