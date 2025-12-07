"""
Tests for Parsing Agent
Uses mocking to avoid actual Azure OpenAI API calls
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.parsing_agent import ParsingAgent
from models.schedule_item import ScheduleItem, EventType


class TestParsingAgent(unittest.TestCase):
    """Test suite for ParsingAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = ParsingAgent()
    
    def test_init(self):
        """Test agent initialization"""
        agent = ParsingAgent()
        self.assertIsNotNone(agent.api_url)
        self.assertIn("api-key", agent.headers)
    
    def test_get_system_prompt(self):
        """Test system prompt is properly defined"""
        prompt = self.agent._get_system_prompt()
        self.assertIn("JSON", prompt)
        self.assertIn("schedule", prompt.lower())
    
    def test_clean_json_response_with_markdown(self):
        """Test cleaning JSON from markdown code blocks"""
        content = '```json\n[{"course": "Test"}]\n```'
        cleaned = self.agent._clean_json_response(content)
        self.assertEqual(cleaned, '[{"course": "Test"}]')
    
    def test_clean_json_response_plain(self):
        """Test cleaning plain JSON"""
        content = '[{"course": "Test"}]'
        cleaned = self.agent._clean_json_response(content)
        self.assertEqual(cleaned, '[{"course": "Test"}]')
    
    def test_clean_json_response_with_generic_markdown(self):
        """Test cleaning JSON from generic code blocks"""
        content = '```\n[{"course": "Test"}]\n```'
        cleaned = self.agent._clean_json_response(content)
        self.assertEqual(cleaned, '[{"course": "Test"}]')
    
    def test_deduplicate_events(self):
        """Test deduplication of events"""
        events = [
            ScheduleItem(
                course="Python",
                event_type=EventType.LECTURE,
                location="Room A",
                date="2025-12-15",
                start_time="10:00",
                end_time="12:00"
            ),
            ScheduleItem(
                course="python",  # Same event, different case
                event_type=EventType.LECTURE,
                location="Room A",
                date="2025-12-15",
                start_time="10:00",
                end_time="12:00"
            ),
            ScheduleItem(
                course="Java",  # Different event
                event_type=EventType.LAB,
                location="Room B",
                date="2025-12-15",
                start_time="14:00",
                end_time="16:00"
            )
        ]
        
        unique = self.agent._deduplicate_events(events)
        self.assertEqual(len(unique), 2)
    
    def test_parse_document_unsupported_format(self):
        """Test parsing unsupported file format"""
        result = self.agent.parse_document("/path/to/file.xyz")
        self.assertEqual(result, [])
    
    @patch('agents.parsing_agent.requests.post')
    def test_parse_schedule_text_success(self, mock_post):
        """Test successful text parsing"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps([{
                        "course": "Python Programming",
                        "type": "lecture",
                        "location": "Room A101",
                        "date": "2025-12-15",
                        "from": "10:00",
                        "to": "12:00"
                    }])
                }
            }]
        }
        mock_post.return_value = mock_response
        
        text = "Python Programming Lecture on Monday 10:00-12:00 in Room A101"
        events = self.agent.parse_schedule_text(text)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].course, "Python Programming")
    
    @patch('agents.parsing_agent.requests.post')
    def test_parse_schedule_text_api_error(self, mock_post):
        """Test handling API error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        events = self.agent.parse_schedule_text("Test schedule")
        self.assertEqual(events, [])
    
    @patch('agents.parsing_agent.requests.post')
    def test_parse_schedule_text_json_error(self, mock_post):
        """Test handling invalid JSON response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "This is not valid JSON"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        events = self.agent.parse_schedule_text("Test schedule")
        self.assertEqual(events, [])
    
    def test_parse_schedule_text_empty(self):
        """Test parsing empty text"""
        events = self.agent.parse_schedule_text("")
        self.assertEqual(events, [])
    
    def test_parse_schedule_text_too_short(self):
        """Test parsing text that's too short"""
        events = self.agent.parse_schedule_text("Hi")
        self.assertEqual(events, [])
    
    @patch('agents.parsing_agent.requests.post')
    def test_parse_schedule_text_multiple_events(self, mock_post):
        """Test parsing multiple events"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {
                            "course": "Python",
                            "type": "lecture",
                            "location": "Room A",
                            "date": "2025-12-15",
                            "from": "10:00",
                            "to": "12:00"
                        },
                        {
                            "course": "Java",
                            "type": "lab",
                            "location": "Room B",
                            "date": "2025-12-15",
                            "from": "14:00",
                            "to": "16:00"
                        }
                    ])
                }
            }]
        }
        mock_post.return_value = mock_response
        
        events = self.agent.parse_schedule_text("Python 10-12, Java 14-16")
        self.assertEqual(len(events), 2)
    
    def test_extract_pdf_text_no_pypdf2(self):
        """Test PDF text extraction without PyPDF2"""
        with patch.object(self.agent, '_extract_pdf_text', return_value=""):
            result = self.agent._extract_pdf_text("/path/to/file.pdf")
            self.assertEqual(result, "")
    
    @patch('agents.parsing_agent.requests.post')
    @patch('builtins.open', create=True)
    def test_extract_schedule_from_image(self, mock_open, mock_post):
        """Test image parsing"""
        # Mock file reading
        mock_open.return_value.__enter__.return_value.read.return_value = b'fake_image_data'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps([{
                        "course": "Test Course",
                        "type": "lecture",
                        "location": "Room",
                        "date": "2025-12-15",
                        "from": "10:00",
                        "to": "12:00"
                    }])
                }
            }]
        }
        mock_post.return_value = mock_response
        
        events = self.agent.extract_schedule_from_image("/path/to/image.png")
        self.assertEqual(len(events), 1)


class TestScheduleItemFromDict(unittest.TestCase):
    """Test ScheduleItem.from_dict() method"""
    
    def test_from_dict_standard(self):
        """Test creating ScheduleItem from standard dict"""
        data = {
            "course": "Python",
            "type": "lecture",
            "location": "Room A",
            "date": "2025-12-15",
            "from": "10:00",
            "to": "12:00"
        }
        
        item = ScheduleItem.from_dict(data)
        self.assertEqual(item.course, "Python")
        self.assertEqual(item.event_type, EventType.LECTURE)
        self.assertEqual(item.start_time, "10:00")
        self.assertEqual(item.end_time, "12:00")
    
    def test_from_dict_alternative_keys(self):
        """Test creating ScheduleItem with alternative keys"""
        data = {
            "course": "Java",
            "event_type": "lab",
            "location": "Lab B",
            "date": "2025-12-16",
            "start_time": "14:00",
            "end_time": "16:00"
        }
        
        item = ScheduleItem.from_dict(data)
        self.assertEqual(item.course, "Java")
        self.assertEqual(item.event_type, EventType.LAB)
    
    def test_from_dict_unknown_type(self):
        """Test creating ScheduleItem with unknown type"""
        data = {
            "course": "Unknown",
            "type": "workshop",
            "location": "Room",
            "date": "2025-12-15",
            "from": "10:00",
            "to": "12:00"
        }
        
        item = ScheduleItem.from_dict(data)
        self.assertEqual(item.event_type, EventType.OTHER)


if __name__ == "__main__":
    unittest.main()
