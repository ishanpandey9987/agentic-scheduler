"""
Collaboration Agent - Coordinates between agents for complex scheduling
Handles multi-event changes and conflict resolution negotiation
"""
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schedule_item import ScheduleItem, EventType
from models.conflict import Conflict
from models.change_request import ChangeRequest, ChangeType
from config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    OPENAI_DEPLOYMENT_NAME,
    OPENAI_API_VERSION
)


class CollaborationAgent:
    """
    Orchestrates multiple agents to resolve complex scheduling scenarios.
    
    Capabilities:
    - Coordinate multi-event changes
    - Negotiate conflict resolutions
    - Find optimal time slots
    - Handle batch operations
    """
    
    def __init__(self, calendar_agent=None, change_agent=None, conflict_agent=None):
        self.calendar_agent = calendar_agent
        self.change_agent = change_agent
        self.conflict_agent = conflict_agent
        self.pending_changes: List[ChangeRequest] = []
        
        self.api_url = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={OPENAI_API_VERSION}"
        self.headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY
        }
    
    def set_agents(self, calendar_agent=None, change_agent=None, conflict_agent=None):
        """Set the agent references"""
        if calendar_agent:
            self.calendar_agent = calendar_agent
        if change_agent:
            self.change_agent = change_agent
        if conflict_agent:
            self.conflict_agent = conflict_agent
    
    def add_change(self, change_request: ChangeRequest):
        """Add a change request to the pending queue"""
        self.pending_changes.append(change_request)
        print(f"📋 Added to queue: {change_request.change_type.value} - {change_request.user_message}")
    
    def coordinate_changes(self, schedule: List[ScheduleItem]) -> Dict[str, Any]:
        """
        Coordinate and execute all pending changes.
        Checks for conflicts between pending changes before executing.
        
        Args:
            schedule: Current schedule
        
        Returns:
            Summary of executed changes
        """
        if not self.pending_changes:
            return {"success": True, "message": "No pending changes", "executed": 0}
        
        print(f"\n🤝 Coordinating {len(self.pending_changes)} pending change(s)...")
        
        results = {
            "success": True,
            "executed": 0,
            "failed": 0,
            "conflicts": [],
            "details": []
        }
        
        # Process each change
        for change in self.pending_changes:
            if self.change_agent:
                result = self.change_agent.execute_change(change)
                results["details"].append({
                    "change": change.user_message,
                    "result": result
                })
                
                if result.get("success"):
                    results["executed"] += 1
                else:
                    results["failed"] += 1
                    results["success"] = False
                
                if result.get("conflicts"):
                    results["conflicts"].extend(result["conflicts"])
        
        # Clear pending changes
        self.pending_changes = []
        
        print(f"\n✅ Executed: {results['executed']}, ❌ Failed: {results['failed']}")
        return results
    
    def resolve_conflicts(self, conflicts: List[Conflict], schedule: List[ScheduleItem]) -> Dict[str, Any]:
        """
        Attempt to automatically resolve conflicts.
        
        Args:
            conflicts: List of conflicts to resolve
            schedule: Current schedule
        
        Returns:
            Resolution results
        """
        print(f"\n🔧 Attempting to resolve {len(conflicts)} conflict(s)...")
        
        results = {
            "resolved": 0,
            "unresolved": 0,
            "suggestions": []
        }
        
        for conflict in conflicts:
            resolution = self._suggest_resolution(conflict, schedule)
            results["suggestions"].append({
                "conflict": conflict.message,
                "suggestion": resolution
            })
            
            # For now, just provide suggestions
            # Auto-resolution could be implemented here
            results["unresolved"] += 1
        
        return results
    
    def _suggest_resolution(self, conflict: Conflict, schedule: List[ScheduleItem]) -> str:
        """Generate a resolution suggestion for a conflict"""
        
        # Find free slots on the same day
        if self.conflict_agent:
            free_slots = self.conflict_agent.find_free_slots(
                schedule, 
                conflict.event_a.date,
                duration_minutes=90  # Assume 1.5 hour events
            )
            
            if free_slots:
                slot_str = ", ".join([f"{s[0]}-{s[1]}" for s in free_slots[:3]])
                return f"Available slots on {conflict.event_a.date}: {slot_str}"
        
        return "Consider rescheduling one of the events to a different day"
    
    def find_best_slot(self, schedule: List[ScheduleItem], date: str, duration_minutes: int = 60) -> Optional[Dict[str, str]]:
        """
        Find the best available time slot on a given date.
        
        Args:
            schedule: Current schedule
            date: Target date (YYYY-MM-DD)
            duration_minutes: Required duration
        
        Returns:
            Dictionary with start and end time, or None if no slot found
        """
        if not self.conflict_agent:
            return None
        
        free_slots = self.conflict_agent.find_free_slots(schedule, date, duration_minutes)
        
        if free_slots:
            # Prefer morning slots (9-12), then afternoon (13-17)
            for start, end in free_slots:
                hour = int(start.split(":")[0])
                if 9 <= hour <= 11:
                    return {"start": start, "end": self._add_minutes(start, duration_minutes)}
            
            for start, end in free_slots:
                hour = int(start.split(":")[0])
                if 13 <= hour <= 16:
                    return {"start": start, "end": self._add_minutes(start, duration_minutes)}
            
            # Return first available slot
            start, end = free_slots[0]
            return {"start": start, "end": self._add_minutes(start, duration_minutes)}
        
        return None
    
    def _add_minutes(self, time_str: str, minutes: int) -> str:
        """Add minutes to a time string"""
        from datetime import datetime, timedelta
        dt = datetime.strptime(time_str, "%H:%M")
        dt += timedelta(minutes=minutes)
        return dt.strftime("%H:%M")
    
    def batch_reschedule(self, events: List[ScheduleItem], target_date: str, schedule: List[ScheduleItem]) -> Dict[str, Any]:
        """
        Reschedule multiple events to a target date.
        
        Args:
            events: Events to reschedule
            target_date: Target date (YYYY-MM-DD)
            schedule: Full current schedule
        
        Returns:
            Results of the batch operation
        """
        print(f"\n📦 Batch rescheduling {len(events)} event(s) to {target_date}...")
        
        results = {
            "success": True,
            "rescheduled": 0,
            "failed": 0,
            "details": []
        }
        
        # Sort events by duration (longer events first to ensure they get slots)
        events_sorted = sorted(events, key=lambda e: self._get_duration(e), reverse=True)
        
        for event in events_sorted:
            duration = self._get_duration(event)
            slot = self.find_best_slot(schedule, target_date, duration)
            
            if slot:
                # Create change request
                change = ChangeRequest(
                    change_type=ChangeType.RESCHEDULE,
                    original_event=event,
                    new_details={
                        "date": target_date,
                        "start_time": slot["start"],
                        "end_time": slot["end"]
                    },
                    user_message=f"Batch reschedule {event.course} to {target_date}"
                )
                
                if self.change_agent:
                    result = self.change_agent.execute_change(change)
                    if result.get("success"):
                        results["rescheduled"] += 1
                        # Update schedule for next iteration
                        event.date = target_date
                        event.start_time = slot["start"]
                        event.end_time = slot["end"]
                    else:
                        results["failed"] += 1
                        results["success"] = False
                    
                    results["details"].append({
                        "event": event.course,
                        "slot": f"{slot['start']}-{slot['end']}",
                        "result": result.get("message", "")
                    })
            else:
                results["failed"] += 1
                results["details"].append({
                    "event": event.course,
                    "slot": None,
                    "result": f"No available slot found on {target_date}"
                })
        
        return results
    
    def _get_duration(self, event: ScheduleItem) -> int:
        """Get event duration in minutes"""
        from datetime import datetime
        try:
            start = datetime.strptime(event.start_time, "%H:%M")
            end = datetime.strptime(event.end_time, "%H:%M")
            return int((end - start).total_seconds() / 60)
        except:
            return 60  # Default 1 hour
    
    def negotiate_time(self, schedule: List[ScheduleItem], preferred_times: List[str], duration: int = 60) -> Dict[str, Any]:
        """
        Find the best time from a list of preferences.
        
        Args:
            schedule: Current schedule
            preferred_times: List of preferred dates (YYYY-MM-DD)
            duration: Required duration in minutes
        
        Returns:
            Best available option
        """
        print(f"\n🤝 Negotiating best time from {len(preferred_times)} options...")
        
        options = []
        
        for date in preferred_times:
            slot = self.find_best_slot(schedule, date, duration)
            if slot:
                options.append({
                    "date": date,
                    "start": slot["start"],
                    "end": slot["end"],
                    "score": self._score_slot(slot["start"])
                })
        
        if options:
            # Sort by score (prefer morning slots)
            options.sort(key=lambda x: x["score"], reverse=True)
            best = options[0]
            
            return {
                "success": True,
                "best_option": best,
                "alternatives": options[1:3]
            }
        
        return {
            "success": False,
            "message": "No available slots found in the preferred times"
        }
    
    def _score_slot(self, start_time: str) -> int:
        """Score a time slot (higher = better)"""
        hour = int(start_time.split(":")[0])
        
        # Prefer 9-11 AM
        if 9 <= hour <= 11:
            return 100
        # Then 14-16
        elif 14 <= hour <= 16:
            return 80
        # Then other afternoon
        elif 12 <= hour <= 17:
            return 60
        # Early morning
        elif 8 <= hour < 9:
            return 40
        # Late afternoon/evening
        else:
            return 20
    
    def process_complex_request(self, request: str, schedule: List[ScheduleItem]) -> Dict[str, Any]:
        """
        Process a complex natural language request that may involve multiple operations.
        
        Args:
            request: Natural language request
            schedule: Current schedule
        
        Returns:
            Processing results
        """
        print(f"\n🧠 Processing complex request: \"{request}\"")
        
        # Use AI to break down the request
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": """You are a scheduling assistant. Analyze the user's request and break it down into individual actions.

Current schedule:
""" + self._format_schedule(schedule) + """

Return a JSON object with:
{
    "actions": [
        {"type": "reschedule|cancel|add|modify", "event": "event name", "details": {...}},
        ...
    ],
    "summary": "Brief description of what will be done"
}

Only return valid JSON."""
                },
                {
                    "role": "user",
                    "content": request
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Clean and parse JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                actions = json.loads(content.strip())
                
                print(f"   📋 Identified {len(actions.get('actions', []))} action(s)")
                print(f"   Summary: {actions.get('summary', 'N/A')}")
                
                return {
                    "success": True,
                    "actions": actions.get("actions", []),
                    "summary": actions.get("summary", "")
                }
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        return {"success": False, "message": "Could not process the request"}
    
    def _format_schedule(self, schedule: List[ScheduleItem]) -> str:
        """Format schedule for AI context"""
        if not schedule:
            return "No events scheduled."
        
        lines = []
        for item in sorted(schedule, key=lambda x: (x.date, x.start_time)):
            lines.append(f"- {item.course} on {item.date} {item.start_time}-{item.end_time} at {item.location}")
        
        return "\n".join(lines)