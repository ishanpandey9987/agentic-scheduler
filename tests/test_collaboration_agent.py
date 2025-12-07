"""
Tests for Collaboration Agent
"""
import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.collaboration_agent import CollaborationAgent
from models.schedule_item import ScheduleItem, EventType
from models.conflict import Conflict, ConflictType
from models.change_request import ChangeRequest, ChangeType


class TestCollaborationAgent(unittest.TestCase):
    """Test suite for CollaborationAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = CollaborationAgent()
    
    def test_init(self):
        """Test agent initialization"""
        agent = CollaborationAgent()
        self.assertIsNone(agent.calendar_agent)
        self.assertIsNone(agent.change_agent)
        self.assertIsNone(agent.conflict_agent)
        self.assertEqual(agent.pending_changes, [])
    
    def test_init_with_agents(self):
        """Test agent initialization with other agents"""
        mock_calendar = Mock()
        mock_change = Mock()
        mock_conflict = Mock()
        
        agent = CollaborationAgent(
            calendar_agent=mock_calendar,
            change_agent=mock_change,
            conflict_agent=mock_conflict
        )
        
        self.assertEqual(agent.calendar_agent, mock_calendar)
        self.assertEqual(agent.change_agent, mock_change)
        self.assertEqual(agent.conflict_agent, mock_conflict)
    
    def test_set_agents(self):
        """Test setting agents after initialization"""
        mock_calendar = Mock()
        mock_change = Mock()
        
        self.agent.set_agents(calendar_agent=mock_calendar, change_agent=mock_change)
        
        self.assertEqual(self.agent.calendar_agent, mock_calendar)
        self.assertEqual(self.agent.change_agent, mock_change)
    
    def test_add_change(self):
        """Test adding a change request to queue"""
        event = ScheduleItem(
            course="Test",
            event_type=EventType.LECTURE,
            location="Room",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        
        change = ChangeRequest(
            change_type=ChangeType.RESCHEDULE,
            original_event=event,
            new_details={"date": "2025-12-16"},
            user_message="Move to Tuesday"
        )
        
        self.agent.add_change(change)
        self.assertEqual(len(self.agent.pending_changes), 1)
    
    def test_coordinate_changes_no_pending(self):
        """Test coordinate_changes with no pending changes"""
        result = self.agent.coordinate_changes([])
        
        self.assertTrue(result["success"])
        self.assertEqual(result["executed"], 0)
        self.assertIn("No pending changes", result["message"])
    
    def test_coordinate_changes_with_pending(self):
        """Test coordinate_changes with pending changes"""
        mock_change_agent = Mock()
        mock_change_agent.execute_change.return_value = {"success": True, "message": "Done"}
        self.agent.change_agent = mock_change_agent
        
        event = ScheduleItem(
            course="Test",
            event_type=EventType.LECTURE,
            location="Room",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        
        change = ChangeRequest(
            change_type=ChangeType.RESCHEDULE,
            original_event=event,
            new_details={"date": "2025-12-16"},
            user_message="Move to Tuesday"
        )
        
        self.agent.pending_changes = [change]
        result = self.agent.coordinate_changes([])
        
        self.assertTrue(result["success"])
        self.assertEqual(result["executed"], 1)
        self.assertEqual(len(self.agent.pending_changes), 0)  # Queue cleared
    
    def test_resolve_conflicts(self):
        """Test resolve_conflicts returns suggestions"""
        event_a = ScheduleItem(
            course="Event A",
            event_type=EventType.LECTURE,
            location="Room A",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        event_b = ScheduleItem(
            course="Event B",
            event_type=EventType.LECTURE,
            location="Room B",
            date="2025-12-15",
            start_time="11:00",
            end_time="13:00"
        )
        
        conflict = Conflict(
            conflict_type=ConflictType.TIME_OVERLAP,
            event_a=event_a,
            event_b=event_b,
            severity="high",
            message="Test conflict"
        )
        
        result = self.agent.resolve_conflicts([conflict], [event_a, event_b])
        
        self.assertEqual(result["unresolved"], 1)
        self.assertEqual(len(result["suggestions"]), 1)
    
    def test_find_best_slot_no_conflict_agent(self):
        """Test find_best_slot returns None when no conflict agent"""
        result = self.agent.find_best_slot([], "2025-12-15", 60)
        self.assertIsNone(result)
    
    def test_find_best_slot_with_conflict_agent(self):
        """Test find_best_slot with conflict agent"""
        mock_conflict = Mock()
        mock_conflict.find_free_slots.return_value = [("10:00", "12:00")]
        self.agent.conflict_agent = mock_conflict
        
        result = self.agent.find_best_slot([], "2025-12-15", 60)
        
        self.assertIsNotNone(result)
        self.assertIn("start", result)
        self.assertIn("end", result)
    
    def test_add_minutes(self):
        """Test _add_minutes helper"""
        result = self.agent._add_minutes("10:00", 90)
        self.assertEqual(result, "11:30")
    
    def test_add_minutes_crossing_hour(self):
        """Test _add_minutes crossing hour boundary"""
        result = self.agent._add_minutes("10:30", 60)
        self.assertEqual(result, "11:30")
    
    def test_get_duration(self):
        """Test _get_duration helper"""
        event = ScheduleItem(
            course="Test",
            event_type=EventType.LECTURE,
            location="Room",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        
        duration = self.agent._get_duration(event)
        self.assertEqual(duration, 120)
    
    def test_get_duration_default(self):
        """Test _get_duration returns default on error"""
        event = Mock()
        event.start_time = "invalid"
        event.end_time = "time"
        
        duration = self.agent._get_duration(event)
        self.assertEqual(duration, 60)  # Default
    
    def test_batch_reschedule_no_slots(self):
        """Test batch_reschedule when no slots available"""
        mock_conflict = Mock()
        mock_conflict.find_free_slots.return_value = []
        self.agent.conflict_agent = mock_conflict
        
        events = [
            ScheduleItem(
                course="Test",
                event_type=EventType.LECTURE,
                location="Room",
                date="2025-12-15",
                start_time="10:00",
                end_time="12:00"
            )
        ]
        
        result = self.agent.batch_reschedule(events, "2025-12-20", [])
        
        self.assertEqual(result["rescheduled"], 0)
        self.assertEqual(result["failed"], 1)


class TestChangeRequest(unittest.TestCase):
    """Test suite for ChangeRequest model"""
    
    def test_change_request_creation(self):
        """Test creating a ChangeRequest"""
        event = ScheduleItem(
            course="Test",
            event_type=EventType.LECTURE,
            location="Room",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        
        request = ChangeRequest(
            change_type=ChangeType.RESCHEDULE,
            original_event=event,
            new_details={"date": "2025-12-16"},
            user_message="Move to Tuesday"
        )
        
        self.assertEqual(request.change_type, ChangeType.RESCHEDULE)
        self.assertEqual(request.user_message, "Move to Tuesday")
    
    def test_change_types(self):
        """Test all change types"""
        types = [
            ChangeType.RESCHEDULE,
            ChangeType.CANCEL,
            ChangeType.MODIFY,
            ChangeType.ADD
        ]
        
        for change_type in types:
            self.assertIsNotNone(change_type.value)


if __name__ == "__main__":
    unittest.main()
