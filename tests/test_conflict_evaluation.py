"""
Tests for Conflict Evaluation Agent
"""
import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.conflict_evaluation_agent import ConflictEvaluationAgent
from models.schedule_item import ScheduleItem, EventType
from models.conflict import Conflict, ConflictType


class TestConflictEvaluationAgent(unittest.TestCase):
    """Test suite for ConflictEvaluationAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = ConflictEvaluationAgent()
    
    def test_init(self):
        """Test agent initialization"""
        agent = ConflictEvaluationAgent()
        self.assertEqual(agent.existing_events, [])
    
    def test_init_with_events(self):
        """Test agent initialization with existing events"""
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
        agent = ConflictEvaluationAgent(existing_events=events)
        self.assertEqual(len(agent.existing_events), 1)
    
    def test_set_events(self):
        """Test setting events"""
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
        self.agent.set_events(events)
        self.assertEqual(len(self.agent.existing_events), 1)
    
    def test_no_conflict(self):
        """Test no conflict when events don't overlap"""
        event1 = ScheduleItem(
            course="Math 101",
            event_type=EventType.LECTURE,
            location="Room A",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        event2 = ScheduleItem(
            course="History 101",
            event_type=EventType.LECTURE,
            location="Room B",
            date="2025-12-15",
            start_time="13:00",
            end_time="15:00"
        )
        
        conflicts = self.agent.check_conflicts([event1, event2])
        self.assertEqual(conflicts, [])
    
    def test_conflict_time_overlap(self):
        """Test conflict detection for overlapping times"""
        event1 = ScheduleItem(
            course="Math 101",
            event_type=EventType.LECTURE,
            location="Room A",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        event2 = ScheduleItem(
            course="Math 102",
            event_type=EventType.LECTURE,
            location="Room B",
            date="2025-12-15",
            start_time="11:00",
            end_time="13:00"
        )
        
        conflicts = self.agent.check_conflicts([event1, event2])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, ConflictType.TIME_OVERLAP)
    
    def test_conflict_double_booking(self):
        """Test conflict detection for exact same time slot"""
        event1 = ScheduleItem(
            course="Math 101",
            event_type=EventType.LECTURE,
            location="Room A",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        event2 = ScheduleItem(
            course="Physics 101",
            event_type=EventType.LECTURE,
            location="Room B",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        
        conflicts = self.agent.check_conflicts([event1, event2])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, ConflictType.DOUBLE_BOOKING)
    
    def test_conflict_back_to_back(self):
        """Test conflict detection for back-to-back events at different locations"""
        event1 = ScheduleItem(
            course="Math 101",
            event_type=EventType.LECTURE,
            location="Building A",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        event2 = ScheduleItem(
            course="Physics 101",
            event_type=EventType.LECTURE,
            location="Building B",
            date="2025-12-15",
            start_time="12:00",
            end_time="14:00"
        )
        
        conflicts = self.agent.check_conflicts([event1, event2])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, ConflictType.BACK_TO_BACK)
    
    def test_multiple_conflicts(self):
        """Test detection of multiple conflicts"""
        event1 = ScheduleItem(
            course="Event 1",
            event_type=EventType.LECTURE,
            location="Room A",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        event2 = ScheduleItem(
            course="Event 2",
            event_type=EventType.LECTURE,
            location="Room B",
            date="2025-12-15",
            start_time="11:00",
            end_time="13:00"
        )
        event3 = ScheduleItem(
            course="Event 3",
            event_type=EventType.LECTURE,
            location="Room C",
            date="2025-12-15",
            start_time="12:00",
            end_time="14:00"
        )
        
        conflicts = self.agent.check_conflicts([event1, event2, event3])
        self.assertGreater(len(conflicts), 1)
    
    def test_no_conflict_different_days(self):
        """Test no conflict when events are on different days"""
        event1 = ScheduleItem(
            course="Math 101",
            event_type=EventType.LECTURE,
            location="Room A",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        event2 = ScheduleItem(
            course="Math 101",
            event_type=EventType.LECTURE,
            location="Room A",
            date="2025-12-16",
            start_time="10:00",
            end_time="12:00"
        )
        
        conflicts = self.agent.check_conflicts([event1, event2])
        self.assertEqual(conflicts, [])
    
    def test_check_new_event_conflicts(self):
        """Test checking conflicts for a new event"""
        existing = [
            ScheduleItem(
                course="Existing Event",
                event_type=EventType.LECTURE,
                location="Room A",
                date="2025-12-15",
                start_time="10:00",
                end_time="12:00"
            )
        ]
        
        new_event = ScheduleItem(
            course="New Event",
            event_type=EventType.LECTURE,
            location="Room B",
            date="2025-12-15",
            start_time="11:00",
            end_time="13:00"
        )
        
        conflicts = self.agent.check_new_event_conflicts(new_event, existing)
        self.assertEqual(len(conflicts), 1)
    
    def test_flag_conflicts_no_conflicts(self):
        """Test flag_conflicts message when no conflicts"""
        events = [
            ScheduleItem(
                course="Event",
                event_type=EventType.LECTURE,
                location="Room",
                date="2025-12-15",
                start_time="10:00",
                end_time="12:00"
            )
        ]
        
        message = self.agent.flag_conflicts(events)
        self.assertIn("No conflicts", message)
    
    def test_flag_conflicts_with_conflicts(self):
        """Test flag_conflicts message when conflicts exist"""
        events = [
            ScheduleItem(
                course="Event 1",
                event_type=EventType.LECTURE,
                location="Room A",
                date="2025-12-15",
                start_time="10:00",
                end_time="12:00"
            ),
            ScheduleItem(
                course="Event 2",
                event_type=EventType.LECTURE,
                location="Room B",
                date="2025-12-15",
                start_time="11:00",
                end_time="13:00"
            )
        ]
        
        message = self.agent.flag_conflicts(events)
        self.assertIn("conflict", message.lower())
    
    def test_find_free_slots_empty_day(self):
        """Test finding free slots on an empty day"""
        schedule = []
        slots = self.agent.find_free_slots(schedule, "2025-12-15", duration_minutes=60)
        
        # Should have at least one free slot (entire day from 08:00 to 20:00)
        self.assertGreater(len(slots), 0)
    
    def test_find_free_slots_busy_day(self):
        """Test finding free slots on a busy day"""
        schedule = [
            ScheduleItem(
                course="Morning",
                event_type=EventType.LECTURE,
                location="Room",
                date="2025-12-15",
                start_time="09:00",
                end_time="11:00"
            ),
            ScheduleItem(
                course="Afternoon",
                event_type=EventType.LECTURE,
                location="Room",
                date="2025-12-15",
                start_time="14:00",
                end_time="16:00"
            )
        ]
        
        slots = self.agent.find_free_slots(schedule, "2025-12-15", duration_minutes=60)
        
        # Should find slots: 08:00-09:00, 11:00-14:00, 16:00-20:00
        self.assertGreater(len(slots), 0)
    
    def test_find_free_slots_filters_by_duration(self):
        """Test that free slots meet minimum duration"""
        schedule = [
            ScheduleItem(
                course="Event",
                event_type=EventType.LECTURE,
                location="Room",
                date="2025-12-15",
                start_time="08:30",  # Only 30 min gap at start
                end_time="19:30"     # Only 30 min gap at end
            )
        ]
        
        # Looking for 60-minute slots
        slots = self.agent.find_free_slots(schedule, "2025-12-15", duration_minutes=60)
        
        # 30-minute gaps shouldn't be returned
        for start, end in slots:
            from datetime import datetime
            start_dt = datetime.strptime(start, "%H:%M")
            end_dt = datetime.strptime(end, "%H:%M")
            duration = (end_dt - start_dt).total_seconds() / 60
            self.assertGreaterEqual(duration, 60)


class TestConflictModel(unittest.TestCase):
    """Test suite for Conflict model"""
    
    def test_conflict_creation(self):
        """Test creating a Conflict"""
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
            message="Test conflict message"
        )
        
        self.assertEqual(conflict.conflict_type, ConflictType.TIME_OVERLAP)
        self.assertEqual(conflict.severity, "high")


if __name__ == "__main__":
    unittest.main()
