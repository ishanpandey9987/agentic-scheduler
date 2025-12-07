from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    from models.schedule_item import ScheduleItem
except ImportError:
    from .schedule_item import ScheduleItem


class ConflictType(Enum):
    """Types of scheduling conflicts"""
    TIME_OVERLAP = "time_overlap"  # Two events at same time
    LOCATION_CONFLICT = "location_conflict"  # Same room, different events
    BACK_TO_BACK = "back_to_back"  # No travel time between locations
    DOUBLE_BOOKING = "double_booking"  # Exact same slot


@dataclass
class Conflict:
    """Represents a scheduling conflict between events"""
    conflict_type: ConflictType
    event_a: ScheduleItem
    event_b: ScheduleItem
    severity: str  # "high", "medium", "low"
    message: str
    suggested_resolution: Optional[str] = None

    def __str__(self):
        return f"Conflict ({self.conflict_type.value}): {self.message}"

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "type": self.conflict_type.value,
            "event_a": self.event_a.to_dict(),
            "event_b": self.event_b.to_dict(),
            "severity": self.severity,
            "message": self.message,
            "suggested_resolution": self.suggested_resolution
        }

    def get_conflict_details(self):
        """Legacy method for backward compatibility"""
        return {
            "event1": str(self.event_a),
            "event2": str(self.event_b),
            "conflict_message": self.message,
            "type": self.conflict_type.value,
            "severity": self.severity
        }