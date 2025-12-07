from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class EventType(Enum):
    """Types of calendar events"""
    LECTURE = "lecture"
    LAB = "lab"
    EXAM = "exam"
    MEETING = "meeting"
    PRACTICE = "practice"
    OTHER = "other"


@dataclass
class ScheduleItem:
    """Represents a single calendar event/schedule item"""
    course: str
    event_type: EventType
    location: str
    date: str  # YYYY-MM-DD format
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    event_id: Optional[str] = None  # Google Calendar event ID
    description: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API calls"""
        return {
            "course": self.course,
            "type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "location": self.location,
            "date": self.date,
            "from": self.start_time,
            "to": self.end_time,
            "event_id": self.event_id,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleItem":
        """Create ScheduleItem from dictionary (parsed from LLM response)"""
        # Handle different key names for event type
        event_type_str = data.get("type") or data.get("event_type") or "other"
        
        # Convert string to EventType enum
        try:
            event_type = EventType(event_type_str.lower())
        except (ValueError, AttributeError):
            event_type = EventType.OTHER
        
        # Handle different key names for time fields
        start_time = data.get("from") or data.get("start_time") or "00:00"
        end_time = data.get("to") or data.get("end_time") or "00:00"
        
        return cls(
            course=data.get("course", "Untitled Event"),
            event_type=event_type,
            location=data.get("location", ""),
            date=data.get("date", ""),
            start_time=start_time,
            end_time=end_time,
            event_id=data.get("event_id"),
            description=data.get("description")
        )

    def get_start_datetime(self) -> datetime:
        """Get start as datetime object"""
        return datetime.strptime(f"{self.date} {self.start_time}", "%Y-%m-%d %H:%M")

    def get_end_datetime(self) -> datetime:
        """Get end as datetime object"""
        return datetime.strptime(f"{self.date} {self.end_time}", "%Y-%m-%d %H:%M")

    def __str__(self):
        event_type_str = self.event_type.value if isinstance(self.event_type, EventType) else self.event_type
        return f"{self.course} ({event_type_str}) at {self.location} on {self.date} from {self.start_time} to {self.end_time}"