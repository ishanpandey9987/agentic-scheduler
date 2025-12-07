"""
Change Management Agent - Handles user requests for schedule changes
Uses OpenAI function calling for natural language understanding
"""
import sys
import json
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schedule_item import ScheduleItem, EventType
from models.change_request import ChangeRequest, ChangeType
from config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    OPENAI_DEPLOYMENT_NAME,
    OPENAI_API_VERSION
)


class ChangeManagementAgent:
    """
    Handles user change requests using natural language processing.
    
    Capabilities:
    - Interpret natural language requests ("move X to Tuesday")
    - Reschedule events
    - Cancel events
    - Modify event details
    - Add new events
    """
    
    def __init__(self, calendar_agent=None, conflict_agent=None):
        self.calendar_agent = calendar_agent
        self.conflict_agent = conflict_agent
        self.current_schedule: List[ScheduleItem] = []
        
        self.api_url = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={OPENAI_API_VERSION}"
        self.headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY
        }
    
    def set_schedule(self, schedule: List[ScheduleItem]):
        """Set the current schedule context"""
        self.current_schedule = schedule
    
    def set_calendar_agent(self, calendar_agent):
        """Set the calendar agent for executing changes"""
        self.calendar_agent = calendar_agent
    
    def set_conflict_agent(self, conflict_agent):
        """Set the conflict agent for checking conflicts"""
        self.conflict_agent = conflict_agent
    
    def _get_tools(self) -> List[dict]:
        """Define function calling tools for the AI"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "reschedule_event",
                    "description": "Move an event to a different date and/or time",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_name": {
                                "type": "string",
                                "description": "Name of the event to reschedule"
                            },
                            "original_date": {
                                "type": "string",
                                "description": "Current date of the event (YYYY-MM-DD)"
                            },
                            "new_date": {
                                "type": "string",
                                "description": "New date for the event (YYYY-MM-DD)"
                            },
                            "new_start_time": {
                                "type": "string",
                                "description": "New start time (HH:MM), optional - keeps original if not specified"
                            },
                            "new_end_time": {
                                "type": "string",
                                "description": "New end time (HH:MM), optional - keeps original if not specified"
                            }
                        },
                        "required": ["event_name", "new_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_event",
                    "description": "Cancel/delete an event from the schedule",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_name": {
                                "type": "string",
                                "description": "Name of the event to cancel"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date of the event (YYYY-MM-DD), optional if event name is unique"
                            }
                        },
                        "required": ["event_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "modify_event",
                    "description": "Modify event details like location or name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_name": {
                                "type": "string",
                                "description": "Name of the event to modify"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date of the event (YYYY-MM-DD)"
                            },
                            "new_location": {
                                "type": "string",
                                "description": "New location for the event"
                            },
                            "new_name": {
                                "type": "string",
                                "description": "New name for the event"
                            }
                        },
                        "required": ["event_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_event",
                    "description": "Add a new event to the schedule",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_name": {
                                "type": "string",
                                "description": "Name of the new event"
                            },
                            "event_type": {
                                "type": "string",
                                "enum": ["lecture", "lab", "exam", "meeting", "practice", "other"],
                                "description": "Type of event"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date (YYYY-MM-DD)"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "Start time (HH:MM)"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "End time (HH:MM)"
                            },
                            "location": {
                                "type": "string",
                                "description": "Location of the event"
                            }
                        },
                        "required": ["event_name", "date", "start_time", "end_time"]
                    }
                }
            }
        ]
    
    def _build_schedule_context(self) -> str:
        """Build schedule context for the AI"""
        if not self.current_schedule:
            return "No events in current schedule."
        
        context = "Current Schedule:\n"
        for item in self.current_schedule:
            event_type = item.event_type.value if isinstance(item.event_type, EventType) else str(item.event_type)
            context += f"- {item.course} ({event_type}) on {item.date} from {item.start_time} to {item.end_time} at {item.location}\n"
        return context
    
    def process_request(self, user_message: str) -> ChangeRequest:
        """
        Process a natural language change request.
        
        Args:
            user_message: Natural language request like "Move Python class to Tuesday"
        
        Returns:
            ChangeRequest object with the interpreted action
        """
        schedule_context = self._build_schedule_context()
        
        # Get current date dynamically
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": f"""You are a schedule management assistant. The user wants to make changes to their schedule.

{schedule_context}

Interpret the user's request and call the appropriate function to make the change.

IMPORTANT RULES:
1. For ADD requests: Use the add_event function even if some details are missing. Make reasonable assumptions:
   - If no end_time given but duration mentioned (e.g., "1 hour"), calculate end_time
   - If no location given, use empty string
   - If event_type not specified, use "meeting" or "other"
   
2. For RESCHEDULE/MOVE requests: Use reschedule_event function
3. For CANCEL/DELETE requests: Use cancel_event function
4. For MODIFY requests (change location, name): Use modify_event function

5. NEVER ask for clarification if you can make a reasonable assumption.
6. Convert relative dates: "tomorrow" = next day, "friday" = next Friday, etc.
7. Convert 12-hour to 24-hour format: "2pm" = "14:00", "12:30pm" = "12:30"

Today's date is {current_date}. Use this to calculate relative dates."""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "tools": self._get_tools(),
            "tool_choice": "auto",
            "temperature": 0.1
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ API error: {response.status_code}")
                return None
            
            result = response.json()
            message = result["choices"][0]["message"]
            
            # Process function calls
            if "tool_calls" in message and message["tool_calls"]:
                tool_call = message["tool_calls"][0]
                function_name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])
                
                return self._create_change_request(function_name, args, user_message)
            
            # No function call - AI asked for clarification
            # Try to parse the request ourselves for common add patterns
            clarification = message.get("content", "Could not understand the request")
            print(f"❓ {clarification}")
            
            # Check if this looks like an add request and try to parse it
            user_lower = user_message.lower()
            if any(word in user_lower for word in ['add', 'schedule', 'create', 'book', 'set up']):
                # This was an add request but AI couldn't parse it fully
                # Return a special type that indicates clarification needed for ADD
                return ChangeRequest(
                    change_type=ChangeType.ADD,
                    original_event=None,
                    new_details={"clarification_needed": clarification, "partial_request": user_message},
                    user_message=user_message,
                    requires_confirmation=True
                )
            
            # For other types, return modify with clarification
            return ChangeRequest(
                change_type=ChangeType.MODIFY,
                original_event=None,
                new_details={"clarification_needed": clarification},
                user_message=user_message,
                requires_confirmation=True
            )
            
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            return None
    
    def _create_change_request(self, function_name: str, args: dict, user_message: str) -> ChangeRequest:
        """Create a ChangeRequest from function call"""
        
        # Find matching event
        original_event = self._find_event(
            args.get("event_name"), 
            args.get("date") or args.get("original_date")
        )
        
        if function_name == "reschedule_event":
            return ChangeRequest(
                change_type=ChangeType.RESCHEDULE,
                original_event=original_event,
                new_details={
                    "date": args.get("new_date"),
                    "start_time": args.get("new_start_time"),
                    "end_time": args.get("new_end_time")
                },
                user_message=user_message
            )
        
        elif function_name == "cancel_event":
            return ChangeRequest(
                change_type=ChangeType.CANCEL,
                original_event=original_event,
                new_details={},
                user_message=user_message
            )
        
        elif function_name == "modify_event":
            return ChangeRequest(
                change_type=ChangeType.MODIFY,
                original_event=original_event,
                new_details={
                    "location": args.get("new_location"),
                    "course": args.get("new_name")
                },
                user_message=user_message
            )
        
        elif function_name == "add_event":
            new_item = ScheduleItem(
                course=args.get("event_name"),
                event_type=EventType(args.get("event_type", "other")),
                location=args.get("location", ""),
                date=args.get("date"),
                start_time=args.get("start_time"),
                end_time=args.get("end_time")
            )
            return ChangeRequest(
                change_type=ChangeType.ADD,
                original_event=None,
                new_details={"new_event": new_item},
                user_message=user_message
            )
        
        return None
    
    def _find_event(self, event_name: str, date: str = None) -> Optional[ScheduleItem]:
        """Find an event by name and optionally date with fuzzy matching"""
        if not event_name:
            return None
        
        event_name_lower = event_name.lower()
        
        # First try exact substring match in local schedule
        for item in self.current_schedule:
            if event_name_lower in item.course.lower():
                if date is None or item.date == date:
                    return item
        
        # Try reverse match (course name in search term)
        for item in self.current_schedule:
            if item.course.lower() in event_name_lower:
                if date is None or item.date == date:
                    return item
        
        # Try fuzzy matching - check if words overlap
        search_words = set(event_name_lower.split())
        best_match = None
        best_score = 0
        
        for item in self.current_schedule:
            course_words = set(item.course.lower().split())
            # Count overlapping words
            overlap = len(search_words & course_words)
            if overlap > best_score:
                if date is None or item.date == date:
                    best_score = overlap
                    best_match = item
        
        # Return best match if at least one word matches
        if best_score > 0:
            return best_match
        
        # If not found locally, search Google Calendar
        if self.calendar_agent:
            return self._search_calendar_with_selection(event_name, date)
        
        return None
    
    def _search_calendar_with_selection(self, keyword: str, date: str = None) -> Optional[ScheduleItem]:
        """
        Search Google Calendar for events matching keyword.
        If multiple matches, prompt user to select.
        """
        if not self.calendar_agent:
            return None
        
        # Search for events
        matches = self.calendar_agent.search_events_by_keyword(keyword)
        
        if not matches:
            return None
        
        # Filter by date if specified
        if date:
            matches = [m for m in matches if m.date == date]
        
        if not matches:
            return None
        
        # If only one match, return it
        if len(matches) == 1:
            print(f"   📍 Found event: {matches[0].course} ({matches[0].date} {matches[0].start_time})")
            return matches[0]
        
        # Multiple matches - prompt user to select
        print(f"\n   🔍 Found {len(matches)} events matching '{keyword}':")
        print("   " + "-" * 50)
        
        for i, event in enumerate(matches[:10], 1):  # Limit to 10 options
            print(f"   [{i}] {event.course}")
            print(f"       📅 {event.date} | ⏰ {event.start_time}-{event.end_time}")
            if event.location:
                print(f"       📍 {event.location}")
        
        print("   [0] Cancel operation")
        print("   " + "-" * 50)
        print(f"\n   Select event (1-{min(len(matches), 10)}) or 0 to cancel: ", end="")
        
        try:
            choice = input().strip()
            
            if choice == '0' or choice.lower() == 'cancel':
                print("   ❌ Operation cancelled.")
                return None
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(matches):
                    selected = matches[index]
                    print(f"   ✅ Selected: {selected.course}")
                    return selected
                else:
                    print("   ⚠️ Invalid selection. Operation cancelled.")
                    return None
            except ValueError:
                print("   ⚠️ Invalid input. Operation cancelled.")
                return None
                
        except EOFError:
            # Non-interactive mode - return first match
            print(f"\n   (Auto-selecting first match: {matches[0].course})")
            return matches[0]
    
    def _get_available_events(self) -> str:
        """Get a formatted list of available events for error messages"""
        if not self.current_schedule:
            return "No events in current schedule."
        
        events_list = []
        for item in self.current_schedule:
            events_list.append(f"  • {item.course} ({item.date} {item.start_time})")
        
        return "\n".join(events_list[:10])  # Limit to 10 events
    
    def execute_change(self, change_request: ChangeRequest, auto_confirm: bool = False) -> Dict[str, Any]:
        """
        Execute a change request.
        
        Args:
            change_request: The change to execute
            auto_confirm: If True, skip user confirmation prompts
        
        Returns:
            Dictionary with success status and message
        """
        if not change_request:
            return {"success": False, "message": "No change request provided"}
        
        result = {"success": False, "message": "", "conflicts": [], "skipped": False}
        
        # Check for duplicates first (for ADD operations)
        if change_request.change_type == ChangeType.ADD:
            new_event = change_request.new_details.get("new_event")
            if new_event:
                # Check if event already exists in local schedule
                for existing in self.current_schedule:
                    if (existing.course.lower() == new_event.course.lower() and
                        existing.date == new_event.date and
                        existing.start_time == new_event.start_time):
                        result["success"] = False
                        result["skipped"] = True
                        result["message"] = f"⚠️ Duplicate: '{new_event.course}' already exists on {new_event.date} at {new_event.start_time}"
                        print(f"   {result['message']}")
                        return result
        
        # Check for conflicts (for reschedule and add)
        if change_request.change_type in [ChangeType.RESCHEDULE, ChangeType.ADD]:
            if self.conflict_agent:
                if change_request.change_type == ChangeType.ADD:
                    new_event = change_request.new_details.get("new_event")
                else:
                    # Create a temporary event with new details
                    original = change_request.original_event
                    if original:
                        # Calculate preserved duration if only start time changed
                        from datetime import datetime as dt
                        original_start = dt.strptime(original.start_time, "%H:%M")
                        original_end = dt.strptime(original.end_time, "%H:%M")
                        original_duration = original_end - original_start
                        
                        new_start_time = change_request.new_details.get("start_time") or original.start_time
                        new_end_time = change_request.new_details.get("end_time")
                        
                        # If only start_time changed, calculate new end_time based on duration
                        if change_request.new_details.get("start_time") and not new_end_time:
                            new_start_dt = dt.strptime(new_start_time, "%H:%M")
                            new_end_dt = new_start_dt + original_duration
                            new_end_time = new_end_dt.strftime("%H:%M")
                        elif not new_end_time:
                            new_end_time = original.end_time
                        
                        new_event = ScheduleItem(
                            course=original.course,
                            event_type=original.event_type,
                            location=original.location,
                            date=change_request.new_details.get("date") or original.date,
                            start_time=new_start_time,
                            end_time=new_end_time
                        )
                    else:
                        new_event = None
                
                if new_event:
                    # Get schedule to check against - use local schedule or Google Calendar
                    check_schedule = [e for e in self.current_schedule if e != change_request.original_event]
                    
                    # If local schedule is empty, get events from Google Calendar for the target date
                    if not check_schedule and self.calendar_agent:
                        target_date = new_event.date
                        calendar_events = self.calendar_agent.get_events(target_date, target_date)
                        # Exclude the event being rescheduled
                        check_schedule = [e for e in calendar_events 
                                         if e.event_id != (change_request.original_event.event_id if change_request.original_event else None)]
                    
                    conflicts = self.conflict_agent.check_new_event_conflicts(new_event, check_schedule)
                    
                    if conflicts:
                        result["conflicts"] = conflicts
                        print(f"\n   ⚠️ {len(conflicts)} conflict(s) detected:")
                        for c in conflicts:
                            print(f"      • {c.message}")
                        
                        # Prompt user for confirmation unless auto_confirm is True
                        if not auto_confirm:
                            print("\n   Do you want to proceed anyway? (y/n): ", end="")
                            try:
                                user_input = input().strip().lower()
                                if user_input not in ['y', 'yes']:
                                    result["success"] = False
                                    result["skipped"] = True
                                    result["message"] = "❌ Operation cancelled by user due to conflicts"
                                    return result
                                print("   Proceeding with the change...")
                            except EOFError:
                                # Non-interactive mode, skip
                                print("\n   (Non-interactive mode: proceeding with change)")
        
        # Execute the change
        if change_request.change_type == ChangeType.CANCEL:
            if change_request.original_event:
                if self.calendar_agent and change_request.original_event.event_id:
                    success = self.calendar_agent.delete_event(change_request.original_event.event_id)
                    result["success"] = success
                    result["message"] = "✅ Event cancelled" if success else "❌ Failed to cancel event"
                else:
                    # Remove from local schedule
                    if change_request.original_event in self.current_schedule:
                        self.current_schedule.remove(change_request.original_event)
                    result["success"] = True
                    result["message"] = f"✅ Cancelled: {change_request.original_event.course}"
            else:
                available = self._get_available_events()
                result["message"] = f"❌ Event not found in your schedule.\n\n📋 Available events:\n{available}" if available != "No events in current schedule." else "❌ No events in schedule. Upload a schedule first or add events."
        
        elif change_request.change_type == ChangeType.RESCHEDULE:
            if change_request.original_event:
                # Update the event
                original = change_request.original_event
                
                # Calculate original duration to preserve it
                from datetime import datetime as dt, timedelta
                original_start = dt.strptime(original.start_time, "%H:%M")
                original_end = dt.strptime(original.end_time, "%H:%M")
                original_duration = original_end - original_start
                
                # Update date if provided
                original.date = change_request.new_details.get("date") or original.date
                
                # Update start time if provided
                new_start = change_request.new_details.get("start_time")
                if new_start:
                    original.start_time = new_start
                    # If end time not explicitly provided, preserve duration
                    new_end = change_request.new_details.get("end_time")
                    if not new_end:
                        new_start_dt = dt.strptime(new_start, "%H:%M")
                        new_end_dt = new_start_dt + original_duration
                        original.end_time = new_end_dt.strftime("%H:%M")
                    else:
                        original.end_time = new_end
                else:
                    # Only update end time if explicitly provided
                    if change_request.new_details.get("end_time"):
                        original.end_time = change_request.new_details.get("end_time")
                
                if self.calendar_agent and original.event_id:
                    success = self.calendar_agent.update_event(original.event_id, original)
                    result["success"] = success
                    result["message"] = f"✅ Rescheduled: {original.course} to {original.date} {original.start_time}-{original.end_time}" if success else "❌ Failed to reschedule"
                else:
                    result["success"] = True
                    result["message"] = f"✅ Rescheduled: {original.course} to {original.date} {original.start_time}-{original.end_time}"
            else:
                available = self._get_available_events()
                result["message"] = f"❌ Event not found in your schedule.\n\n📋 Available events:\n{available}" if available != "No events in current schedule." else "❌ No events in schedule. Upload a schedule first or add events."
        
        elif change_request.change_type == ChangeType.ADD:
            new_event = change_request.new_details.get("new_event")
            
            # Check if this is a clarification request (AI couldn't fully parse)
            if change_request.new_details.get("clarification_needed"):
                clarification = change_request.new_details.get("clarification_needed")
                result["success"] = False
                result["message"] = f"ℹ️ {clarification}\n\n💡 Please try again with more details, e.g.:\n   'Add dentist appointment on 2025-12-12 from 12:30 to 13:30'"
                return result
            
            if new_event:
                # Check if already in local schedule (double-check)
                already_exists = any(
                    e.course.lower() == new_event.course.lower() and
                    e.date == new_event.date and
                    e.start_time == new_event.start_time
                    for e in self.current_schedule
                )
                
                if already_exists:
                    result["success"] = False
                    result["skipped"] = True
                    result["message"] = f"⚠️ Skipped: '{new_event.course}' already in schedule for {new_event.date} at {new_event.start_time}"
                elif self.calendar_agent:
                    # Calendar agent will check for duplicates in Google Calendar
                    event_id = self.calendar_agent.create_event(new_event, check_duplicates=True)
                    if event_id:
                        new_event.event_id = event_id
                        # Only add to local schedule if not already there
                        if not already_exists:
                            self.current_schedule.append(new_event)
                        result["success"] = True
                        result["message"] = f"✅ Added: {new_event.course} on {new_event.date}"
                    else:
                        result["message"] = "❌ Failed to add event to calendar"
                else:
                    if not already_exists:
                        self.current_schedule.append(new_event)
                    result["success"] = True
                    result["message"] = f"✅ Added: {new_event.course} on {new_event.date}"
            else:
                result["message"] = "❌ No event details provided. Please specify: event name, date, start time, and end time."
        
        elif change_request.change_type == ChangeType.MODIFY:
            # Check if this is a clarification request
            if change_request.new_details.get("clarification_needed"):
                clarification = change_request.new_details.get("clarification_needed")
                result["success"] = False
                result["message"] = f"ℹ️ {clarification}"
                return result
            
            if change_request.original_event:
                original = change_request.original_event
                if change_request.new_details.get("location"):
                    original.location = change_request.new_details["location"]
                if change_request.new_details.get("course"):
                    original.course = change_request.new_details["course"]
                
                if self.calendar_agent and original.event_id:
                    success = self.calendar_agent.update_event(original.event_id, original)
                    result["success"] = success
                    result["message"] = f"✅ Modified: {original.course}" if success else "❌ Failed to modify"
                else:
                    result["success"] = True
                    result["message"] = f"✅ Modified: {original.course}"
            else:
                result["message"] = "❌ Event not found. Use 'show' to see your current schedule."
        
        return result
    
    def process_and_execute(self, user_message: str, auto_confirm: bool = False) -> Dict[str, Any]:
        """
        Process a natural language request and execute the change.
        Convenience method that combines process_request and execute_change.
        
        Args:
            user_message: Natural language request
            auto_confirm: If True, skip user confirmation prompts for conflicts
        
        Returns:
            Result dictionary with success status and message
        """
        print(f"\n📝 Processing: \"{user_message}\"")
        
        change_request = self.process_request(user_message)
        
        if change_request:
            print(f"   Interpreted as: {change_request.change_type.value}")
            if change_request.original_event:
                print(f"   Target event: {change_request.original_event.course}")
            
            return self.execute_change(change_request, auto_confirm=auto_confirm)
        
        return {"success": False, "message": "Could not process the request"}
    
    def notify_users(self, change_request: ChangeRequest):
        """Notify users about changes (placeholder for future implementation)"""
        print(f"📢 Notification: {change_request.change_type.value} - {change_request.user_message}")