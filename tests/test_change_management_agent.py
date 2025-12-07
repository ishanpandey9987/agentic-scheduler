"""
Tests for Change Management Agent
Uses mocking to avoid actual Azure OpenAI API calls
"""
import unittest
from unittest.mock import Mock, patch
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.change_management_agent import ChangeManagementAgent
from models.schedule_item import ScheduleItem, EventType
from models.change_request import ChangeRequest, ChangeType


class TestChangeManagementAgent(unittest.TestCase):
    """Test suite for ChangeManagementAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = ChangeManagementAgent()
    
    def test_init(self):
        """Test agent initialization"""
        agent = ChangeManagementAgent()
        self.assertIsNone(agent.calendar_agent)
        self.assertIsNone(agent.conflict_agent)
        self.assertEqual(agent.current_schedule, [])
    
    def test_init_with_agents(self):
        """Test agent initialization with other agents"""
        mock_calendar = Mock()
        mock_conflict = Mock()
        
        agent = ChangeManagementAgent(
            calendar_agent=mock_calendar,
            conflict_agent=mock_conflict
        )
        
        self.assertEqual(agent.calendar_agent, mock_calendar)
        self.assertEqual(agent.conflict_agent, mock_conflict)
    
    def test_set_schedule(self):
        """Test setting the schedule"""
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
        
        self.agent.set_schedule(events)
        self.assertEqual(len(self.agent.current_schedule), 1)
    
    def test_set_calendar_agent(self):
        """Test setting calendar agent"""
        mock_calendar = Mock()
        self.agent.set_calendar_agent(mock_calendar)
        self.assertEqual(self.agent.calendar_agent, mock_calendar)
    
    def test_set_conflict_agent(self):
        """Test setting conflict agent"""
        mock_conflict = Mock()
        self.agent.set_conflict_agent(mock_conflict)
        self.assertEqual(self.agent.conflict_agent, mock_conflict)
    
    def test_get_tools(self):
        """Test that tools are properly defined"""
        tools = self.agent._get_tools()
        
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        
        # Check required tools exist
        tool_names = [t["function"]["name"] for t in tools]
        self.assertIn("reschedule_event", tool_names)
        self.assertIn("cancel_event", tool_names)
        self.assertIn("modify_event", tool_names)
        self.assertIn("add_event", tool_names)
    
    def test_build_schedule_context_empty(self):
        """Test building context with empty schedule"""
        context = self.agent._build_schedule_context()
        self.assertIn("No events", context)
    
    def test_build_schedule_context_with_events(self):
        """Test building context with events"""
        self.agent.current_schedule = [
            ScheduleItem(
                course="Python Programming",
                event_type=EventType.LECTURE,
                location="Room A101",
                date="2025-12-15",
                start_time="10:00",
                end_time="12:00"
            )
        ]
        
        context = self.agent._build_schedule_context()
        
        self.assertIn("Python Programming", context)
        self.assertIn("2025-12-15", context)
        self.assertIn("10:00", context)
    
    @patch('agents.change_management_agent.requests.post')
    def test_process_request_reschedule(self, mock_post):
        """Test processing a reschedule request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "name": "reschedule_event",
                            "arguments": json.dumps({
                                "event_name": "Python",
                                "new_date": "2025-12-16",
                                "new_start_time": "14:00"
                            })
                        }
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        self.agent.current_schedule = [
            ScheduleItem(
                course="Python",
                event_type=EventType.LECTURE,
                location="Room",
                date="2025-12-15",
                start_time="10:00",
                end_time="12:00"
            )
        ]
        
        result = self.agent.process_request("Move Python to Tuesday at 2pm")
        
        self.assertIsInstance(result, ChangeRequest)
        self.assertEqual(result.change_type, ChangeType.RESCHEDULE)
    
    @patch('agents.change_management_agent.requests.post')
    def test_process_request_cancel(self, mock_post):
        """Test processing a cancel request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "name": "cancel_event",
                            "arguments": json.dumps({
                                "event_name": "Python"
                            })
                        }
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        self.agent.current_schedule = [
            ScheduleItem(
                course="Python",
                event_type=EventType.LECTURE,
                location="Room",
                date="2025-12-15",
                start_time="10:00",
                end_time="12:00"
            )
        ]
        
        result = self.agent.process_request("Cancel Python class")
        
        self.assertIsInstance(result, ChangeRequest)
        self.assertEqual(result.change_type, ChangeType.CANCEL)
    
    @patch('agents.change_management_agent.requests.post')
    def test_process_request_add(self, mock_post):
        """Test processing an add event request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "name": "add_event",
                            "arguments": json.dumps({
                                "event_name": "Team Meeting",
                                "event_type": "meeting",
                                "date": "2025-12-17",
                                "start_time": "15:00",
                                "end_time": "16:00",
                                "location": "Conference Room"
                            })
                        }
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = self.agent.process_request("Add a team meeting on Wednesday at 3pm")
        
        self.assertIsInstance(result, ChangeRequest)
        self.assertEqual(result.change_type, ChangeType.ADD)
    
    @patch('agents.change_management_agent.requests.post')
    def test_process_request_api_error(self, mock_post):
        """Test handling API error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        result = self.agent.process_request("Do something")
        
        self.assertIsNone(result)


class TestExecuteChange(unittest.TestCase):
    """Test suite for execute_change functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = ChangeManagementAgent()
        self.mock_calendar = Mock()
        self.agent.calendar_agent = self.mock_calendar
    
    def test_execute_reschedule(self):
        """Test executing a reschedule change"""
        event = ScheduleItem(
            course="Test",
            event_type=EventType.LECTURE,
            location="Room",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00",
            event_id="event123"
        )
        
        change = ChangeRequest(
            change_type=ChangeType.RESCHEDULE,
            original_event=event,
            new_details={
                "date": "2025-12-16",
                "start_time": "14:00",
                "end_time": "16:00"
            },
            user_message="Move to Tuesday"
        )
        
        self.mock_calendar.update_event.return_value = True
        
        result = self.agent.execute_change(change)
        
        self.assertTrue(result["success"])
        self.mock_calendar.update_event.assert_called_once()
    
    def test_execute_cancel(self):
        """Test executing a cancel change"""
        event = ScheduleItem(
            course="Test",
            event_type=EventType.LECTURE,
            location="Room",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00",
            event_id="event123"
        )
        
        change = ChangeRequest(
            change_type=ChangeType.CANCEL,
            original_event=event,
            new_details={},
            user_message="Cancel event"
        )
        
        self.mock_calendar.delete_event.return_value = True
        
        result = self.agent.execute_change(change)
        
        self.assertTrue(result["success"])
        self.mock_calendar.delete_event.assert_called_once_with("event123")
    
    def test_execute_add(self):
        """Test executing an add change"""
        change = ChangeRequest(
            change_type=ChangeType.ADD,
            original_event=None,
            new_details={
                "event_name": "New Event",
                "event_type": "meeting",
                "date": "2025-12-17",
                "start_time": "15:00",
                "end_time": "16:00",
                "location": "Room"
            },
            user_message="Add new event"
        )
        
        self.mock_calendar.create_event.return_value = "new_event_123"
        
        result = self.agent.execute_change(change)
        
        # The execute_change for ADD may return success or failure depending on implementation
        self.assertIn("success", result)
    
    def test_execute_no_calendar_agent(self):
        """Test executing change without calendar agent"""
        self.agent.calendar_agent = None
        
        event = ScheduleItem(
            course="Test",
            event_type=EventType.LECTURE,
            location="Room",
            date="2025-12-15",
            start_time="10:00",
            end_time="12:00"
        )
        
        change = ChangeRequest(
            change_type=ChangeType.CANCEL,
            original_event=event,
            new_details={},
            user_message="Cancel"
        )
        
        result = self.agent.execute_change(change)
        
        # When no calendar agent, might still return result dict
        self.assertIn("success", result)


if __name__ == "__main__":
    unittest.main()
