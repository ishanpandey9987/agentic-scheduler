# filepath: /agentic-scheduler/agentic-scheduler/src/models/__init__.py
"""
Models package - Data structures for the Agentic Scheduler
"""
try:
    from models.schedule_item import ScheduleItem, EventType
    from models.conflict import Conflict, ConflictType
    from models.change_request import ChangeRequest, ChangeType
except ImportError:
    from .schedule_item import ScheduleItem, EventType
    from .conflict import Conflict, ConflictType
    from .change_request import ChangeRequest, ChangeType

__all__ = [
    "ScheduleItem",
    "EventType",
    "Conflict",
    "ConflictType",
    "ChangeRequest",
    "ChangeType"
]