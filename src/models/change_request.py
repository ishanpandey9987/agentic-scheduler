from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

try:
    from models.schedule_item import ScheduleItem
except ImportError:
    from .schedule_item import ScheduleItem


class ChangeType(Enum):
    """Types of schedule changes"""
    RESCHEDULE = "reschedule"  # Move to different time
    CANCEL = "cancel"  # Remove event
    MODIFY = "modify"  # Change details (location, name)
    ADD = "add"  # Add new event


@dataclass
class ChangeRequest:
    """Represents a user's request to change the schedule"""
    change_type: ChangeType
    original_event: Optional[ScheduleItem]
    new_details: Dict[str, Any]  # New values for changed fields
    user_message: str  # Original user request
    requires_confirmation: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "change_type": self.change_type.value,
            "original_event": self.original_event.to_dict() if self.original_event else None,
            "new_details": self.new_details,
            "user_message": self.user_message,
            "requires_confirmation": self.requires_confirmation
        }

    def validate(self) -> bool:
        """Validate the change request"""
        if self.change_type == ChangeType.ADD:
            # For ADD, we need new_details with event info
            required_fields = ["course", "date", "start_time", "end_time"]
            new_event = self.new_details.get("new_event", {})
            return all(field in new_event or field in self.new_details for field in required_fields)
        
        elif self.change_type in [ChangeType.RESCHEDULE, ChangeType.MODIFY, ChangeType.CANCEL]:
            # Need an original event to modify
            return self.original_event is not None
        
        return False

    def apply_change(self, calendar_agent=None) -> bool:
        """Apply the change using the calendar agent"""
        if not self.validate():
            print("❌ Change request validation failed")
            return False
        
        if calendar_agent is None:
            print("⚠️ No calendar agent provided")
            return False
        
        # Implementation depends on change type
        # This is handled by ChangeManagementAgent.execute_change()
        return True

    def __repr__(self):
        return f"<ChangeRequest(type={self.change_type.value}, event={self.original_event.course if self.original_event else 'N/A'})>"