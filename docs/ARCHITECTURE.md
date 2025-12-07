# Architecture of the Agentic Scheduler

## Overview

The Agentic Scheduler is a multi-agent system designed to automate the process of converting static schedules into dynamic Google Calendar events. It uses Azure OpenAI for natural language processing and vision capabilities, combined with Google Calendar API for event management.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENTIC SCHEDULER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐    ┌─────────────────────────────────────────────────┐   │
│   │   USER      │    │              MAIN APPLICATION                    │   │
│   │  INTERFACE  │◄──►│  • CLI Mode (Step-by-step workflow)              │   │
│   │             │    │  • Chatbot Mode (Natural language interface)     │   │
│   └─────────────┘    └─────────────────────────────────────────────────┘   │
│                                        │                                    │
│                                        ▼                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         AGENT LAYER                                  │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│   │  │ Parsing  │ │ Calendar │ │  Change  │ │ Conflict │ │ Collab   │   │   │
│   │  │  Agent   │ │  Agent   │ │ Mgmt     │ │  Eval    │ │  Agent   │   │   │
│   │  │          │ │          │ │  Agent   │ │  Agent   │ │          │   │   │
│   │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │   │
│   └───────┼────────────┼────────────┼────────────┼────────────┼─────────┘   │
│           │            │            │            │            │             │
│           ▼            ▼            ▼            ▼            ▼             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      EXTERNAL SERVICES                               │   │
│   │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │   │
│   │  │  Azure OpenAI   │    │ Google Calendar │    │   Local Cache   │  │   │
│   │  │   (GPT-4V)      │    │      API        │    │   (In-Memory)   │  │   │
│   │  └─────────────────┘    └─────────────────┘    └─────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Components

### 1. Parsing Agent (`parsing_agent.py`)

**Purpose**: Extracts schedule information from various file formats using AI vision capabilities.

**Key Features**:
- Supports PNG, JPG, PDF, and DOCX file formats
- Uses Azure OpenAI GPT-4V for vision-based extraction
- Converts images to base64 for API processing
- Returns structured `ScheduleItem` objects

**Key Methods**:
```python
parse_schedule(file_path: str) -> List[ScheduleItem]
parse_image(image_path: str) -> List[ScheduleItem]
parse_pdf(pdf_path: str) -> List[ScheduleItem]
parse_docx(docx_path: str) -> List[ScheduleItem]
```

**Technologies**: Azure OpenAI GPT-4V, base64 encoding, PyPDF2, python-docx

---

### 2. Calendar Agent (`calendar_agent.py`)

**Purpose**: Manages all interactions with Google Calendar API.

**Key Features**:
- OAuth2 authentication with Google
- CRUD operations (Create, Read, Update, Delete)
- Duplicate detection before creating events
- Keyword-based event search
- User selection prompt for multiple matches

**Key Methods**:
```python
authenticate() -> bool
create_event(item: ScheduleItem) -> str  # Returns event_id
create_event_with_duplicate_handling(item: ScheduleItem) -> Dict
update_event(event_id: str, item: ScheduleItem) -> bool
delete_event(event_id: str) -> bool
get_events(start_date: str, end_date: str) -> List[ScheduleItem]
list_upcoming_events(max_results: int) -> List[ScheduleItem]
search_events_by_keyword(keyword: str) -> List[ScheduleItem]
```

**Technologies**: Google Calendar API v3, OAuth2, google-auth libraries

---

### 3. Change Management Agent (`change_management_agent.py`)

**Purpose**: Processes natural language requests for schedule modifications using OpenAI function calling.

**Key Features**:
- Natural language understanding for schedule changes
- OpenAI function calling for structured intent parsing
- Supports: add, reschedule, cancel, modify operations
- Automatic event search from Google Calendar when local cache is empty
- Multi-select prompt when multiple events match

**Key Methods**:
```python
process_request(user_message: str) -> ChangeRequest
execute_change(change_request: ChangeRequest) -> Dict[str, Any]
set_schedule(schedule: List[ScheduleItem]) -> None
```

**Function Definitions** (for OpenAI):
- `reschedule_event(event_name, new_date, new_start_time, new_end_time)`
- `cancel_event(event_name, date)`
- `modify_event(event_name, new_location, new_name)`
- `add_event(event_name, event_type, date, start_time, end_time, location)`

**Technologies**: Azure OpenAI with function calling, intent parsing

---

### 4. Conflict Evaluation Agent (`conflict_evaluation_agent.py`)

**Purpose**: Detects scheduling conflicts and finds available time slots.

**Key Features**:
- Time overlap detection between events
- Free slot finder within working hours (8am-8pm)
- Conflict severity classification
- Supports checking against Google Calendar events

**Key Methods**:
```python
check_conflicts(schedule: List[ScheduleItem]) -> List[Conflict]
check_new_event_conflicts(new_event: ScheduleItem, schedule: List[ScheduleItem]) -> List[Conflict]
find_free_slots(schedule: List[ScheduleItem], date: str, duration_minutes: int) -> List[Tuple]
```

**Technologies**: Python datetime, time interval algorithms

---

### 5. Collaboration Agent (`collaboration_agent.py`)

**Purpose**: Coordinates changes that affect multiple events or require batch operations.

**Key Features**:
- Groups related events for batch processing
- Manages multi-event changes
- Coordinates stakeholder notifications (future feature)

**Key Methods**:
```python
coordinate_changes(changes: List[ChangeRequest]) -> Dict
group_related_events(schedule: List[ScheduleItem]) -> Dict
```

---

## Data Models

### ScheduleItem (`models/schedule_item.py`)
```python
@dataclass
class ScheduleItem:
    course: str                    # Event name/title
    event_type: EventType          # lecture, lab, meeting, etc.
    location: str                  # Physical/virtual location
    date: str                      # YYYY-MM-DD format
    start_time: str                # HH:MM format
    end_time: str                  # HH:MM format
    event_id: Optional[str]        # Google Calendar event ID
    description: Optional[str]     # Additional details
```

### ChangeRequest (`models/change_request.py`)
```python
@dataclass
class ChangeRequest:
    change_type: ChangeType        # ADD, RESCHEDULE, CANCEL, MODIFY
    original_event: Optional[ScheduleItem]
    new_details: Dict[str, Any]
    user_message: str
    requires_confirmation: bool
```

### Conflict (`models/conflict.py`)
```python
@dataclass
class Conflict:
    event1: ScheduleItem
    event2: ScheduleItem
    conflict_type: ConflictType    # TIME_OVERLAP, LOCATION_CONFLICT
    severity: ConflictSeverity     # LOW, MEDIUM, HIGH
    message: str
```

---

## Data Flow Diagrams

### 1. Schedule Parsing Flow
```
┌─────────┐    ┌─────────────┐    ┌──────────────┐    ┌────────────────┐
│  File   │───►│  Parsing    │───►│ Local Cache  │───►│ Google Calendar│
│ Upload  │    │   Agent     │    │ (Preview)    │    │  (Permanent)   │
└─────────┘    └─────────────┘    └──────────────┘    └────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ Azure OpenAI│
              │   GPT-4V    │
              └─────────────┘
```

### 2. Natural Language Change Flow
```
┌─────────────┐    ┌────────────────┐    ┌─────────────┐    ┌──────────────┐
│ User Input  │───►│ Change Mgmt    │───►│ Conflict    │───►│ Calendar     │
│ "Move X to" │    │ Agent (OpenAI) │    │ Eval Agent  │    │ Agent (API)  │
└─────────────┘    └────────────────┘    └─────────────┘    └──────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ Function    │
                   │ Calling     │
                   │ (OpenAI)    │
                   └─────────────┘
```

### 3. Event Search Flow
```
┌─────────────┐    ┌────────────────┐    ┌──────────────────┐
│ Partial     │───►│ Calendar Agent │───►│ User Selection   │
│ Event Name  │    │ Keyword Search │    │ (Multiple Match) │
└─────────────┘    └────────────────┘    └──────────────────┘
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **AI/LLM** | Azure OpenAI GPT-4 | Vision parsing, NLU, function calling |
| **Calendar API** | Google Calendar API v3 | Event CRUD, search, OAuth2 |
| **Backend** | Python 3.11+ | Core application logic |
| **Data Models** | Python dataclasses | Structured data with enums |
| **Authentication** | OAuth2 (Google) | Secure calendar access |
| **Configuration** | python-dotenv | Environment variable management |

---

## Key Design Patterns

1. **Multi-Agent Architecture**: Each agent is a self-contained module with specific responsibilities, enabling modularity and maintainability.

2. **Local Cache + Remote Sync**: Events are staged locally (in-memory) for preview and editing before committing to Google Calendar, reducing API calls and enabling batch operations.

3. **Function Calling**: OpenAI function calling provides structured parsing of natural language requests into actionable operations.

4. **Duplicate Detection**: Before creating events, the system checks for existing duplicates and prompts the user for action (keep, replace, keep both, cancel).

5. **Conflict Resolution**: Automatic time overlap detection with user confirmation before proceeding with conflicting changes.

6. **Graceful Fallback**: When local cache is empty, the system automatically queries Google Calendar for event operations.

---

## File Structure

```
agentic-scheduler/
├── src/
│   ├── main.py                          # Entry point (CLI + Chatbot modes)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── parsing_agent.py             # Image/PDF parsing with GPT-4V
│   │   ├── calendar_agent.py            # Google Calendar integration
│   │   ├── change_management_agent.py   # NLP request handling
│   │   ├── conflict_evaluation_agent.py # Overlap detection
│   │   └── collaboration_agent.py       # Multi-event coordination
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schedule_item.py             # Event data model
│   │   ├── conflict.py                  # Conflict data model
│   │   └── change_request.py            # Change request model
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                  # Configuration loader
│   └── utils/
│       ├── __init__.py
│       ├── formatters.py                # Output formatting
│       ├── validators.py                # Input validation
│       └── logger.py                    # Logging utilities
├── tests/                               # Unit tests for each agent
├── docs/                                # Documentation
│   ├── architecture.md                  # This file
│   ├── setup.md                         # Setup instructions
│   ├── usage.md                         # Usage guide
│   └── api.md                           # API reference
├── examples/
│   └── sample_schedule.py               # Example usage
├── credentials.json                     # Google OAuth credentials (gitignored)
├── token.json                           # Google OAuth token (gitignored)
├── .env                                 # Environment variables (gitignored)
├── .env.example                         # Example environment file
├── requirements.txt                     # Python dependencies
└── README.md                            # Project overview
```
