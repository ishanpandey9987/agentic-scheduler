"""
Tests for Calendar Agent
Uses mocking to avoid actual Google Calendar API calls
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.calendar_agent import CalendarAgent
from models.schedule_item import ScheduleItem, EventType


class TestCalendarAgent(unittest.TestCase):
    """Test suite for CalendarAgent"""
    
    def setUp(self):
        """Set up test fixtures with mocked Google API"""
        self.agent = CalendarAgent()
        # Mock the service to avoid real API calls
        self.agent.service = Mock()
    
    def test_init(self):
        """Test agent initialization"""
        agent = CalendarAgent()
        self.assertIsNone(agent.service)
        self.assertEqual(agent.timezone, "Europe/Brussels")
    
    def test_create_schedule_item(self):
        """Test ScheduleItem creation"""
        item = ScheduleItem(
            course="Python Programming",
            event_type=EventType.LECTURE,
            location="Room A101",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        self.assertEqual(item.course, "Python Programming")
        self.assertEqual(item.event_type, EventType.LECTURE)
        self.assertEqual(item.date, "2025-12-15")
    
    def test_check_duplicate_no_service(self):
        """Test check_duplicate returns None when not authenticated"""
        agent = CalendarAgent()
        agent.service = None
        
        item = ScheduleItem(
            course="Test Event",
            event_type=EventType.LECTURE,
            location="Room A",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        
        with patch.object(agent, 'authenticate', return_value=False):
            result = agent.check_duplicate(item)
        
        self.assertIsNone(result)
    
    def test_check_duplicate_no_duplicates(self):
        """Test check_duplicate returns None when no duplicates exist"""
        # Mock the events().list() response
        mock_events = {
            'items': [
                {
                    'id': '123',
                    'summary': 'Different Event',
                    'start': {'dateTime': '2025-12-15T14:00:00+01:00'},
                    'end': {'dateTime': '2025-12-15T15:00:00+01:00'},
                    'location': 'Room B'
                }
            ]
        }
        self.agent.service.events().list().execute.return_value = mock_events
        
        item = ScheduleItem(
            course="Test Event",
            event_type=EventType.LECTURE,
            location="Room A",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        
        result = self.agent.check_duplicate(item)
        self.assertIsNone(result)
    
    def test_check_duplicate_found(self):
        """Test check_duplicate returns event when duplicate found"""
        mock_events = {
            'items': [
                {
                    'id': '123',
                    'summary': 'Test Event',
                    'start': {'dateTime': '2025-12-15T10:00:00+01:00'},
                    'end': {'dateTime': '2025-12-15T12:00:00+01:00'},
                    'location': 'Room A'
                }
            ]
        }
        self.agent.service.events().list().execute.return_value = mock_events
        
        item = ScheduleItem(
            course="Test Event",
            event_type=EventType.LECTURE,
            location="Room A",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        
        result = self.agent.check_duplicate(item)
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], '123')
    
    def test_list_upcoming_events(self):
        """Test listing upcoming events"""
        mock_events = {
            'items': [
                {
                    'id': '1',
                    'summary': 'Event 1',
                    'start': {'dateTime': '2025-12-15T10:00:00+01:00'},
                    'end': {'dateTime': '2025-12-15T12:00:00+01:00'},
                    'location': 'Room A'
                },
                {
                    'id': '2',
                    'summary': 'Event 2',
                    'start': {'dateTime': '2025-12-16T14:00:00+01:00'},
                    'end': {'dateTime': '2025-12-16T15:00:00+01:00'},
                    'location': 'Room B'
                }
            ]
        }
        self.agent.service.events().list().execute.return_value = mock_events
        
        events = self.agent.list_upcoming_events(max_results=10)
        self.assertEqual(len(events), 2)
    
    def test_search_events_by_keyword(self):
        """Test searching events by keyword"""
        mock_events = {
            'items': [
                {
                    'id': '1',
                    'summary': 'Python Programming Lecture',
                    'start': {'dateTime': '2025-12-15T10:00:00+01:00'},
                    'end': {'dateTime': '2025-12-15T12:00:00+01:00'},
                    'location': 'Room A'
                },
                {
                    'id': '2',
                    'summary': 'Java Workshop',
                    'start': {'dateTime': '2025-12-16T14:00:00+01:00'},
                    'end': {'dateTime': '2025-12-16T15:00:00+01:00'},
                    'location': 'Room B'
                }
            ]
        }
        self.agent.service.events().list().execute.return_value = mock_events
        
        # Should find Python event - search_events_by_keyword returns ScheduleItem objects
        results = self.agent.search_events_by_keyword("python")
        self.assertEqual(len(results), 1)
        self.assertIn('Python', results[0].course)
    
    def test_search_events_by_keyword_no_match(self):
        """Test searching events with no matches"""
        mock_events = {
            'items': [
                {
                    'id': '1',
                    'summary': 'Python Programming',
                    'start': {'dateTime': '2025-12-15T10:00:00+01:00'},
                    'end': {'dateTime': '2025-12-15T12:00:00+01:00'},
                    'location': 'Room A'
                }
            ]
        }
        self.agent.service.events().list().execute.return_value = mock_events
        
        results = self.agent.search_events_by_keyword("mathematics")
        self.assertEqual(len(results), 0)
    
    def test_delete_event_success(self):
        """Test deleting an event"""
        self.agent.service.events().delete().execute.return_value = None
        
        result = self.agent.delete_event("test_event_id")
        self.assertTrue(result)
    
    def test_delete_event_failure(self):
        """Test delete event handles errors"""
        self.agent.service.events().delete().execute.side_effect = Exception("API Error")
        
        result = self.agent.delete_event("invalid_id")
        self.assertFalse(result)
    
    def test_create_event_internal(self):
        """Test internal event creation"""
        mock_created = {'id': 'new_event_123'}
        self.agent.service.events().insert().execute.return_value = mock_created
        
        item = ScheduleItem(
            course="New Event",
            event_type=EventType.MEETING,
            location="Conference Room",
            date="2025-12-20",
            start_time="14:00",
            end_time="15:00"
        )
        
        result = self.agent._create_event_internal(item)
        self.assertEqual(result, 'new_event_123')
    
    def test_update_event_success(self):
        """Test updating an event"""
        self.agent.service.events().update().execute.return_value = {}
        
        item = ScheduleItem(
            course="Updated Event",
            event_type=EventType.LECTURE,
            location="New Room",
            date="2025-12-20",
            start_time="10:00",
            end_time="12:00"
        )
        
        result = self.agent.update_event("event_123", item)
        self.assertTrue(result)
    
    def test_update_event_failure(self):
        """Test update event handles errors"""
        self.agent.service.events().update().execute.side_effect = Exception("API Error")
        
        item = ScheduleItem(
            course="Event",
            event_type=EventType.LECTURE,
            location="Room",
            date="2025-12-20",
            start_time="10:00",
            end_time="12:00"
        )
        
        result = self.agent.update_event("invalid_id", item)
        self.assertFalse(result)
    
    def test_get_events_date_range(self):
        """Test getting events within a date range"""
        mock_events = {
            'items': [
                {
                    'id': '1',
                    'summary': 'Event in Range',
                    'start': {'dateTime': '2025-12-15T10:00:00+01:00'},
                    'end': {'dateTime': '2025-12-15T12:00:00+01:00'},
                    'location': 'Room A'
                }
            ]
        }
        self.agent.service.events().list().execute.return_value = mock_events
        
        events = self.agent.get_events("2025-12-15", "2025-12-20")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].course, 'Event in Range')


class TestScheduleItem(unittest.TestCase):
    """Test suite for ScheduleItem model"""
    
    def test_schedule_item_creation(self):
        """Test creating a ScheduleItem"""
        item = ScheduleItem(
            course="Math 101",
            event_type=EventType.LECTURE,
            location="Building A, Room 101",
            date="2025-12-15",
            start_time="09:00",
            end_time="10:30"
        )
        
        self.assertEqual(item.course, "Math 101")
        self.assertEqual(item.event_type, EventType.LECTURE)
        self.assertEqual(item.location, "Building A, Room 101")
        self.assertEqual(item.date, "2025-12-15")
        self.assertEqual(item.start_time, "09:00")
        self.assertEqual(item.end_time, "10:30")
    
    def test_schedule_item_with_all_event_types(self):
        """Test ScheduleItem with different event types"""
        event_types = [
            EventType.LECTURE,
            EventType.LAB,
            EventType.EXAM,
            EventType.MEETING,
            EventType.PRACTICE,
            EventType.OTHER
        ]
        
        for event_type in event_types:
            item = ScheduleItem(
                course="Test Course",
                event_type=event_type,
                location="Room",
                date="2025-12-15",
                start_time="10:00",
                end_time="11:00"
            )
            self.assertEqual(item.event_type, event_type)
    
    def test_schedule_item_with_event_id(self):
        """Test ScheduleItem with event_id"""
        item = ScheduleItem(
            course="Test",
            event_type=EventType.OTHER,
            location="Room",
            date="2025-12-15",
            start_time="10:00",
            end_time="11:00",
            event_id="abc123"
        )
        self.assertEqual(item.event_id, "abc123")
    
    def test_schedule_item_with_description(self):
        """Test ScheduleItem with description"""
        item = ScheduleItem(
            course="Test",
            event_type=EventType.OTHER,
            location="Room",
            date="2025-12-15",
            start_time="10:00",
            end_time="11:00",
            description="This is a test event"
        )
        self.assertEqual(item.description, "This is a test event")


if __name__ == "__main__":
    unittest.main()
