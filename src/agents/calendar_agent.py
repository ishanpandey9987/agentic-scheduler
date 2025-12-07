"""
Calendar Agent - Manages Google Calendar operations
Handles authentication, CRUD operations for events
"""
import os
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schedule_item import ScheduleItem, EventType
from config.settings import (
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_TOKEN_PATH,
    SCHEDULING_SETTINGS
)

# Google Calendar imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False
    print("⚠️ Google Calendar API not installed. Run: pip install google-api-python-client google-auth-oauthlib")

SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarAgent:
    """
    Manages Google Calendar operations including:
    - Authentication with OAuth2
    - Creating, updating, deleting events
    - Retrieving events for conflict checking
    """
    
    def __init__(self):
        self.service = None
        self.timezone = SCHEDULING_SETTINGS.get("time_zone", "Europe/Brussels")
        self.credentials_path = GOOGLE_CREDENTIALS_PATH
        self.token_path = GOOGLE_TOKEN_PATH
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API using OAuth2.
        Returns True if authentication successful.
        """
        if not HAS_GOOGLE_API:
            print("❌ Google API libraries not installed")
            return False
        
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                print(f"⚠️ Error loading token: {e}")
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("🔄 Token refreshed")
                except Exception as e:
                    print(f"⚠️ Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    print(f"❌ Credentials file not found: {self.credentials_path}")
                    print("   Download from Google Cloud Console → APIs → Credentials")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    print("✅ New authentication successful")
                except Exception as e:
                    print(f"❌ Authentication failed: {e}")
                    return False
            
            # Save token for future use
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        # Build the service
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            print("✅ Connected to Google Calendar")
            return True
        except Exception as e:
            print(f"❌ Failed to build service: {e}")
            return False
    
    def check_duplicate(self, item: ScheduleItem) -> Optional[dict]:
        """
        Check if an event already exists in the calendar.
        Returns dict with event details if duplicate found, None otherwise.
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        # Search for events on the same day
        time_min = f"{item.date}T00:00:00Z"
        time_max = f"{item.date}T23:59:59Z"
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            for event in events:
                summary = event.get('summary', '').lower()
                start = event['start'].get('dateTime', '')
                end = event['end'].get('dateTime', '')
                location = event.get('location', '')
                
                # Check if same name and overlapping time
                if item.course.lower() in summary or summary in item.course.lower():
                    if item.start_time in start:
                        # Parse times for display
                        start_time = start.split('T')[1][:5] if 'T' in start else '00:00'
                        end_time = end.split('T')[1][:5] if 'T' in end else '00:00'
                        
                        return {
                            'id': event.get('id'),
                            'summary': event.get('summary', ''),
                            'start_time': start_time,
                            'end_time': end_time,
                            'location': location,
                            'date': item.date
                        }
                
                # Check for exact time match (same slot)
                if 'T' in start:
                    event_time = start.split('T')[1][:5]  # Get HH:MM
                    if event_time == item.start_time:
                        # Same start time - potential duplicate
                        if item.course.lower() in summary:
                            end_time = end.split('T')[1][:5] if 'T' in end else '00:00'
                            return {
                                'id': event.get('id'),
                                'summary': event.get('summary', ''),
                                'start_time': event_time,
                                'end_time': end_time,
                                'location': location,
                                'date': item.date
                            }
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Could not check for duplicates: {e}")
            return None
    
    def create_event_with_duplicate_handling(self, item: ScheduleItem, auto_mode: str = None) -> dict:
        """
        Create an event with interactive duplicate handling.
        
        Args:
            item: The schedule item to create
            auto_mode: If set, automatically choose: 'new' (replace old), 'old' (keep existing), None (prompt user)
        
        Returns:
            dict with 'event_id', 'action' ('created', 'kept_existing', 'replaced'), and 'message'
        """
        if not self.service:
            if not self.authenticate():
                return {'event_id': None, 'action': 'error', 'message': 'Authentication failed'}
        
        # Check for existing duplicate
        existing = self.check_duplicate(item)
        
        if existing:
            print(f"\n   ⚠️ Similar event found in Google Calendar!")
            print(f"   ┌─────────────────────────────────────────────────────")
            print(f"   │ EXISTING: {existing['summary']}")
            print(f"   │   📅 {existing['date']} | ⏰ {existing['start_time']}-{existing['end_time']}")
            print(f"   │   📍 {existing['location'] or 'No location'}")
            print(f"   ├─────────────────────────────────────────────────────")
            event_type = item.event_type.value if hasattr(item.event_type, 'value') else str(item.event_type)
            print(f"   │ NEW: {item.course} ({event_type})")
            print(f"   │   📅 {item.date} | ⏰ {item.start_time}-{item.end_time}")
            print(f"   │   📍 {item.location or 'No location'}")
            print(f"   └─────────────────────────────────────────────────────")
            
            # Determine action
            if auto_mode:
                choice = auto_mode
                print(f"   Auto-selecting: {choice}")
            else:
                print(f"\n   What would you like to do?")
                print(f"   [1] Keep EXISTING event (discard new proposal)")
                print(f"   [2] Replace with NEW event (delete existing)")
                print(f"   [3] Keep BOTH events")
                print(f"   [4] Cancel operation")
                print(f"\n   Enter choice (1/2/3/4): ", end="")
                
                try:
                    user_input = input().strip()
                    choice = user_input
                except EOFError:
                    choice = '1'  # Default to keeping existing in non-interactive mode
                    print("1 (default - non-interactive)")
            
            if choice in ['1', 'old', 'existing']:
                # Keep existing, discard new
                print(f"   ✅ Keeping existing event. New proposal discarded.")
                return {
                    'event_id': existing['id'],
                    'action': 'kept_existing',
                    'message': f"Kept existing: {existing['summary']}"
                }
            
            elif choice in ['2', 'new', 'replace']:
                # Delete existing, create new
                print(f"   🗑️ Deleting existing event...")
                self.delete_event(existing['id'])
                
                print(f"   ➕ Creating new event...")
                event_id = self._create_event_internal(item)
                if event_id:
                    return {
                        'event_id': event_id,
                        'action': 'replaced',
                        'message': f"Replaced existing with: {item.course}"
                    }
                else:
                    return {
                        'event_id': None,
                        'action': 'error',
                        'message': "Failed to create new event after deleting existing"
                    }
            
            elif choice in ['3', 'both']:
                # Keep both - create new without duplicate check
                print(f"   ➕ Creating new event (keeping both)...")
                event_id = self._create_event_internal(item)
                if event_id:
                    return {
                        'event_id': event_id,
                        'action': 'created_both',
                        'message': f"Created new event while keeping existing"
                    }
                else:
                    return {
                        'event_id': None,
                        'action': 'error',
                        'message': "Failed to create new event"
                    }
            
            else:
                # Cancel
                print(f"   ❌ Operation cancelled.")
                return {
                    'event_id': None,
                    'action': 'cancelled',
                    'message': "Operation cancelled by user"
                }
        
        else:
            # No duplicate, create normally
            event_id = self._create_event_internal(item)
            if event_id:
                return {
                    'event_id': event_id,
                    'action': 'created',
                    'message': f"Created: {item.course}"
                }
            else:
                return {
                    'event_id': None,
                    'action': 'error',
                    'message': "Failed to create event"
                }
    
    def _create_event_internal(self, item: ScheduleItem) -> Optional[str]:
        """Internal method to create event without duplicate checking."""
        event_type_str = item.event_type.value if isinstance(item.event_type, EventType) else str(item.event_type)
        
        event = {
            'summary': f"{item.course} ({event_type_str})",
            'location': item.location,
            'description': item.description or f"Type: {event_type_str}\nAdded by Agentic Scheduler",
            'start': {
                'dateTime': f"{item.date}T{item.start_time}:00",
                'timeZone': self.timezone,
            },
            'end': {
                'dateTime': f"{item.date}T{item.end_time}:00",
                'timeZone': self.timezone,
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        try:
            created_event = self.service.events().insert(
                calendarId='primary', 
                body=event
            ).execute()
            
            event_id = created_event.get('id')
            print(f"   ✅ Created: {item.course} on {item.date} {item.start_time}-{item.end_time}")
            return event_id
            
        except Exception as e:
            print(f"   ❌ Failed to create '{item.course}': {e}")
            return None
    
    def create_event(self, item: ScheduleItem, check_duplicates: bool = True, auto_mode: str = None) -> Optional[str]:
        """
        Create a single event in Google Calendar.
        Returns the event ID if successful, None otherwise.
        
        Args:
            item: The schedule item to create
            check_duplicates: If True, checks for existing duplicates first
            auto_mode: For duplicates - 'new' (replace), 'old' (keep existing), 'both', None (prompt)
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        # Use the new duplicate handling method
        if check_duplicates:
            result = self.create_event_with_duplicate_handling(item, auto_mode)
            return result.get('event_id')
        else:
            return self._create_event_internal(item)
    
    def create_events_batch(self, items: List[ScheduleItem]) -> List[str]:
        """
        Create multiple events in Google Calendar.
        Returns list of created event IDs.
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        created_ids = []
        print(f"\n📅 Adding {len(items)} events to Google Calendar...")
        
        for item in items:
            event_id = self.create_event(item)
            if event_id:
                item.event_id = event_id
                created_ids.append(event_id)
        
        print(f"\n✅ Successfully added {len(created_ids)}/{len(items)} events")
        return created_ids
    
    def update_event(self, event_id: str, item: ScheduleItem) -> bool:
        """
        Update an existing event in Google Calendar.
        """
        if not self.service:
            if not self.authenticate():
                return False
        
        event_type_str = item.event_type.value if isinstance(item.event_type, EventType) else str(item.event_type)
        
        # Clean course name - remove multiple (other) or (type) annotations
        import re
        course_name = item.course
        # Remove all existing type annotations like (lecture), (lab), (other), etc.
        course_name = re.sub(r'\s*\([a-zA-Z]+\)\s*', ' ', course_name)
        course_name = course_name.strip()
        
        # Add the current event type
        summary = f"{course_name} ({event_type_str})"
        
        event = {
            'summary': summary,
            'location': item.location,
            'description': item.description or f"Type: {event_type_str}\nUpdated by Agentic Scheduler",
            'start': {
                'dateTime': f"{item.date}T{item.start_time}:00",
                'timeZone': self.timezone,
            },
            'end': {
                'dateTime': f"{item.date}T{item.end_time}:00",
                'timeZone': self.timezone,
            },
        }
        
        try:
            self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            print(f"   ✅ Updated: {course_name}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to update '{course_name}': {e}")
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event from Google Calendar.
        """
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            print(f"   ✅ Deleted event: {event_id}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to delete event: {e}")
            return False
    
    def get_events(self, start_date: str, end_date: str) -> List[ScheduleItem]:
        """
        Retrieve events from Google Calendar within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            List of ScheduleItem objects
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        time_min = f"{start_date}T00:00:00Z"
        time_max = f"{end_date}T23:59:59Z"
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            schedule_items = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Parse datetime
                if 'T' in start:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    date_str = start_dt.strftime('%Y-%m-%d')
                    start_time = start_dt.strftime('%H:%M')
                    end_time = end_dt.strftime('%H:%M')
                else:
                    date_str = start
                    start_time = "00:00"
                    end_time = "23:59"
                
                item = ScheduleItem(
                    course=event.get('summary', 'Untitled'),
                    event_type=EventType.OTHER,
                    location=event.get('location', ''),
                    date=date_str,
                    start_time=start_time,
                    end_time=end_time,
                    event_id=event.get('id'),
                    description=event.get('description', '')
                )
                schedule_items.append(item)
            
            return schedule_items
            
        except Exception as e:
            print(f"❌ Failed to get events: {e}")
            return []
    
    def list_upcoming_events(self, max_results: int = 10) -> List[ScheduleItem]:
        """
        List upcoming events from now.
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        now = datetime.utcnow().isoformat() + 'Z'
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                print('No upcoming events found.')
                return []
            
            schedule_items = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                if 'T' in start:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    date_str = start_dt.strftime('%Y-%m-%d')
                    start_time = start_dt.strftime('%H:%M')
                else:
                    date_str = start
                    start_time = "00:00"
                
                item = ScheduleItem(
                    course=event.get('summary', 'Untitled'),
                    event_type=EventType.OTHER,
                    location=event.get('location', ''),
                    date=date_str,
                    start_time=start_time,
                    end_time="00:00",
                    event_id=event.get('id')
                )
                schedule_items.append(item)
            
            return schedule_items
            
        except Exception as e:
            print(f"❌ Failed to list events: {e}")
            return []
    
    def search_events_by_keyword(self, keyword: str, max_results: int = 20) -> List[ScheduleItem]:
        """
        Search for events containing a keyword in their title.
        
        Args:
            keyword: Search term to find in event titles
            max_results: Maximum number of events to search through
        
        Returns:
            List of matching ScheduleItem objects
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        # Search from 30 days ago to 60 days in the future
        from datetime import timedelta
        now = datetime.utcnow()
        time_min = (now - timedelta(days=30)).isoformat() + 'Z'
        time_max = (now + timedelta(days=60)).isoformat() + 'Z'
        
        try:
            # Use Google Calendar's search query
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                q=keyword,  # Search query
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return []
            
            schedule_items = []
            keyword_lower = keyword.lower()
            
            for event in events:
                summary = event.get('summary', '')
                
                # Additional filtering - check if keyword is in summary
                if keyword_lower in summary.lower():
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    
                    if 'T' in start:
                        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                        date_str = start_dt.strftime('%Y-%m-%d')
                        start_time = start_dt.strftime('%H:%M')
                        end_time = end_dt.strftime('%H:%M')
                    else:
                        date_str = start
                        start_time = "00:00"
                        end_time = "23:59"
                    
                    item = ScheduleItem(
                        course=summary,
                        event_type=EventType.OTHER,
                        location=event.get('location', ''),
                        date=date_str,
                        start_time=start_time,
                        end_time=end_time,
                        event_id=event.get('id'),
                        description=event.get('description', '')
                    )
                    schedule_items.append(item)
            
            return schedule_items
            
        except Exception as e:
            print(f"❌ Failed to search events: {e}")
            return []