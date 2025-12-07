# API Reference for Agentic Scheduler

## Overview

This document provides API reference for the internal Python classes and methods used in the Agentic Scheduler. These are not REST APIs, but Python class interfaces that can be used programmatically.

---

## Parsing Agent API

### Class: `ParsingAgent`

**Location**: `src/agents/parsing_agent.py`

#### Constructor

```python
ParsingAgent()
```

Creates a new Parsing Agent instance. Automatically loads Azure OpenAI configuration from environment variables.

#### Methods

##### `parse_schedule(file_path: str) -> List[ScheduleItem]`

Main entry point for parsing any supported file format.

**Parameters**:
- `file_path` (str): Absolute path to the file to parse

**Returns**: List of `ScheduleItem` objects

**Supported formats**: PNG, JPG, JPEG, PDF, DOCX

**Example**:
```python
from agents.parsing_agent import ParsingAgent

agent = ParsingAgent()
events = agent.parse_schedule("/path/to/schedule.png")
for event in events:
    print(f"{event.course} on {event.date} at {event.start_time}")
```

##### `parse_image(image_path: str) -> List[ScheduleItem]`

Parse an image file using GPT-4V vision.

**Parameters**:
- `image_path` (str): Path to PNG/JPG image

**Returns**: List of `ScheduleItem` objects

##### `parse_pdf(pdf_path: str) -> List[ScheduleItem]`

Parse a PDF file by converting pages to images.

**Parameters**:
- `pdf_path` (str): Path to PDF file

**Returns**: List of `ScheduleItem` objects

##### `parse_docx(docx_path: str) -> List[ScheduleItem]`

Parse a Word document text content.

**Parameters**:
- `docx_path` (str): Path to DOCX file

**Returns**: List of `ScheduleItem` objects

---

## Calendar Agent API

### Class: `CalendarAgent`

**Location**: `src/agents/calendar_agent.py`

#### Constructor

```python
CalendarAgent(timezone: str = "Europe/Brussels")
```

**Parameters**:
- `timezone` (str): Timezone for calendar events (default: Europe/Brussels)

#### Methods

##### `authenticate() -> bool`

Authenticate with Google Calendar API using OAuth2.

**Returns**: `True` if authentication successful, `False` otherwise

**Side effects**: Creates `token.json` on first authentication

**Example**:
```python
from agents.calendar_agent import CalendarAgent

agent = CalendarAgent()
if agent.authenticate():
    print("Connected to Google Calendar")
```

##### `create_event(item: ScheduleItem) -> str`

Create a new event in Google Calendar.

**Parameters**:
- `item` (ScheduleItem): Event details

**Returns**: Google Calendar event ID

**Example**:
```python
from models.schedule_item import ScheduleItem, EventType

event = ScheduleItem(
    course="Team Meeting",
    event_type=EventType.MEETING,
    location="Room A",
    date="2025-12-10",
    start_time="14:00",
    end_time="15:00"
)
event_id = agent.create_event(event)
```

##### `create_event_with_duplicate_handling(item: ScheduleItem) -> Dict`

Create event with duplicate detection and user prompts.

**Parameters**:
- `item` (ScheduleItem): Event details

**Returns**: Dictionary with:
- `success` (bool): Whether event was created
- `event_id` (str): Google Calendar event ID (if created)
- `action` (str): Action taken (created, skipped, replaced)

##### `update_event(event_id: str, item: ScheduleItem) -> bool`

Update an existing event.

**Parameters**:
- `event_id` (str): Google Calendar event ID
- `item` (ScheduleItem): Updated event details

**Returns**: `True` if successful

##### `delete_event(event_id: str) -> bool`

Delete an event from Google Calendar.

**Parameters**:
- `event_id` (str): Google Calendar event ID

**Returns**: `True` if successful

##### `get_events(start_date: str, end_date: str) -> List[ScheduleItem]`

Get events within a date range.

**Parameters**:
- `start_date` (str): Start date (YYYY-MM-DD)
- `end_date` (str): End date (YYYY-MM-DD)

**Returns**: List of `ScheduleItem` objects

**Example**:
```python
events = agent.get_events("2025-12-01", "2025-12-31")
```

##### `list_upcoming_events(max_results: int = 10) -> List[ScheduleItem]`

List upcoming events from current time.

**Parameters**:
- `max_results` (int): Maximum number of events to return

**Returns**: List of `ScheduleItem` objects

##### `search_events_by_keyword(keyword: str, max_results: int = 20) -> List[ScheduleItem]`

Search for events containing a keyword.

**Parameters**:
- `keyword` (str): Search term
- `max_results` (int): Maximum results

**Returns**: List of matching `ScheduleItem` objects

**Example**:
```python
matches = agent.search_events_by_keyword("calculus")
for match in matches:
    print(f"Found: {match.course} on {match.date}")
```

---

## Change Management Agent API

### Class: `ChangeManagementAgent`

**Location**: `src/agents/change_management_agent.py`

#### Constructor

```python
ChangeManagementAgent(
    conflict_agent: ConflictEvaluationAgent = None,
    calendar_agent: CalendarAgent = None
)
```

**Parameters**:
- `conflict_agent`: Optional conflict evaluation agent for conflict checking
- `calendar_agent`: Optional calendar agent for Google Calendar integration

#### Methods

##### `set_schedule(schedule: List[ScheduleItem]) -> None`

Set the current working schedule (local cache).

**Parameters**:
- `schedule` (List[ScheduleItem]): List of events

##### `process_request(user_message: str) -> ChangeRequest`

Process a natural language request using OpenAI function calling.

**Parameters**:
- `user_message` (str): Natural language request

**Returns**: `ChangeRequest` object with parsed intent

**Example**:
```python
from agents.change_management_agent import ChangeManagementAgent

agent = ChangeManagementAgent()
request = agent.process_request("Move calculus to Friday at 2pm")
print(f"Action: {request.change_type}")
print(f"Target: {request.original_event}")
print(f"New details: {request.new_details}")
```

##### `execute_change(change_request: ChangeRequest, auto_confirm: bool = False) -> Dict`

Execute a change request.

**Parameters**:
- `change_request` (ChangeRequest): The change to execute
- `auto_confirm` (bool): Skip user confirmation for conflicts

**Returns**: Dictionary with:
- `success` (bool): Whether change was applied
- `message` (str): Result message
- `conflicts` (List): Any detected conflicts

---

## Conflict Evaluation Agent API

### Class: `ConflictEvaluationAgent`

**Location**: `src/agents/conflict_evaluation_agent.py`

#### Constructor

```python
ConflictEvaluationAgent()
```

#### Methods

##### `check_conflicts(schedule: List[ScheduleItem]) -> List[Conflict]`

Check for conflicts in a schedule.

**Parameters**:
- `schedule` (List[ScheduleItem]): List of events to check

**Returns**: List of `Conflict` objects

**Example**:
```python
from agents.conflict_evaluation_agent import ConflictEvaluationAgent

agent = ConflictEvaluationAgent()
conflicts = agent.check_conflicts(schedule)
for conflict in conflicts:
    print(f"Conflict: {conflict.message}")
```

##### `check_new_event_conflicts(new_event: ScheduleItem, schedule: List[ScheduleItem]) -> List[Conflict]`

Check if a new event conflicts with existing schedule.

**Parameters**:
- `new_event` (ScheduleItem): Event to check
- `schedule` (List[ScheduleItem]): Existing events

**Returns**: List of conflicts with the new event

##### `find_free_slots(schedule: List[ScheduleItem], date: str, duration_minutes: int = 60) -> List[Tuple[str, str]]`

Find free time slots on a specific date.

**Parameters**:
- `schedule` (List[ScheduleItem]): Current schedule
- `date` (str): Date to check (YYYY-MM-DD)
- `duration_minutes` (int): Minimum slot duration

**Returns**: List of (start_time, end_time) tuples

**Example**:
```python
slots = agent.find_free_slots(schedule, "2025-12-10", duration_minutes=60)
for start, end in slots:
    print(f"Free: {start} - {end}")
```

---

## Data Models

### ScheduleItem

**Location**: `src/models/schedule_item.py`

```python
@dataclass
class ScheduleItem:
    course: str                        # Event name/title
    event_type: EventType              # Type of event
    location: str                      # Physical/virtual location
    date: str                          # Date (YYYY-MM-DD)
    start_time: str                    # Start time (HH:MM)
    end_time: str                      # End time (HH:MM)
    event_id: Optional[str] = None     # Google Calendar event ID
    description: Optional[str] = None  # Additional details
```

### EventType Enum

```python
class EventType(Enum):
    LECTURE = "lecture"
    LAB = "lab"
    PRACTICE = "practice"
    MEETING = "meeting"
    WORKSHOP = "workshop"
    SEMINAR = "seminar"
    EXAM = "exam"
    OTHER = "other"
```

### ChangeRequest

**Location**: `src/models/change_request.py`

```python
@dataclass
class ChangeRequest:
    change_type: ChangeType            # Type of change
    original_event: Optional[ScheduleItem]
    new_details: Dict[str, Any]
    user_message: str
    requires_confirmation: bool = True
```

### ChangeType Enum

```python
class ChangeType(Enum):
    ADD = "add"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    MODIFY = "modify"
```

### Conflict

**Location**: `src/models/conflict.py`

```python
@dataclass
class Conflict:
    event1: ScheduleItem
    event2: ScheduleItem
    conflict_type: ConflictType
    severity: ConflictSeverity
    message: str
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_API_KEY` | Yes | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint URL |
| `OPENAI_MODEL_NAME` | Yes | Model name (e.g., gpt-4o) |
| `OPENAI_DEPLOYMENT_NAME` | Yes | Deployment name |
| `OPENAI_VERSION_NAME` | Yes | API version |
| `TIMEZONE` | No | Timezone (default: Europe/Brussels) |
| `LOG_LEVEL` | No | Logging level (default: DEBUG) |
| `DEBUG_MODE` | No | Enable debug mode (default: True) |

---

## Error Handling

All agents use try-except blocks and return appropriate error messages. Common exceptions:

```python
# Authentication error
try:
    agent.authenticate()
except Exception as e:
    print(f"Authentication failed: {e}")

# API error
try:
    events = agent.get_events("2025-12-01", "2025-12-31")
except Exception as e:
    print(f"API error: {e}")
```

---

## Usage Example

Complete example using multiple agents:

```python
from agents.parsing_agent import ParsingAgent
from agents.calendar_agent import CalendarAgent
from agents.change_management_agent import ChangeManagementAgent
from agents.conflict_evaluation_agent import ConflictEvaluationAgent

# Initialize agents
parsing_agent = ParsingAgent()
calendar_agent = CalendarAgent()
conflict_agent = ConflictEvaluationAgent()
change_agent = ChangeManagementAgent(conflict_agent, calendar_agent)

# Authenticate with Google Calendar
calendar_agent.authenticate()

# Parse a schedule file
events = parsing_agent.parse_schedule("/path/to/schedule.png")

# Check for conflicts
conflicts = conflict_agent.check_conflicts(events)
if conflicts:
    print(f"Found {len(conflicts)} conflicts")

# Sync to Google Calendar
for event in events:
    result = calendar_agent.create_event_with_duplicate_handling(event)
    print(f"{event.course}: {result['action']}")

# Process natural language change
change_agent.set_schedule(events)
request = change_agent.process_request("Move calculus to Friday at 2pm")
result = change_agent.execute_change(request)
print(result['message'])
```
