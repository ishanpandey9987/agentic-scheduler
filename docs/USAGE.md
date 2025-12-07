# Usage Guide for Agentic Scheduler

## Overview

The Agentic Scheduler provides two operation modes:
1. **CLI Mode** - Step-by-step guided workflow for batch processing
2. **Chatbot Mode** - Natural language conversation interface

---

## Starting the Application

```bash
cd agentic-scheduler
python src/main.py
```

You'll see the mode selection menu:

```
============================================================
   📅 AGENTIC SCHEDULER
   Intelligent Schedule Management System
============================================================

   Select Mode:

   [1] 📝 CLI Mode - Step-by-step guided workflow
   [2] 🤖 Chatbot Mode - Natural conversation interface
   [3] ❌ Exit
```

---

## Mode 1: CLI Mode

CLI Mode is ideal for batch processing schedule files and systematic workflow.

### Workflow Steps:

1. **Upload Schedule File**
   - Supports: PNG, JPG, PDF, DOCX
   - The Parsing Agent extracts events using AI vision

2. **Review Parsed Events**
   - View extracted schedule items
   - Edit or correct any misidentified information

3. **Check Conflicts**
   - The Conflict Evaluation Agent detects overlapping events
   - Review and resolve conflicts before syncing

4. **Sync to Google Calendar**
   - Events are created in your Google Calendar
   - Duplicate detection prevents creating existing events

### Example Session:

```
📁 Enter file path: /path/to/schedule.png

🔍 Parsing schedule...
✅ Found 5 events:

   1. Calculus (lecture)
      📅 2025-12-08 | ⏰ 08:15-10:15 | 📍 Room A101

   2. Python Programming (lab)
      📅 2025-12-08 | ⏰ 13:30-15:30 | 📍 Computer Lab B

   ...

⚠️ 1 conflict detected:
   • Time overlap: 'Meeting' overlaps with 'Calculus'

Continue with sync? (y/n): y

✅ 5 events synced to Google Calendar
```

---

## Mode 2: Chatbot Mode

Chatbot Mode provides a natural language interface for managing your calendar.

### Available Commands:

| Command | Description | Example |
|---------|-------------|---------|
| `upload` / `parse` | Upload a schedule file | `upload` |
| `show` / `schedule` | Display local schedule cache | `show` |
| `events` | List upcoming Google Calendar events | `events` |
| `search [keyword]` | Search events by keyword | `search calculus` |
| `conflicts` | Check for scheduling conflicts | `conflicts` |
| `free slots` | Find available time slots | `free slots` |
| `clear` | Clear local cache (not Google Calendar) | `clear` |
| `help` | Show help message | `help` |
| `quit` / `exit` | Exit chatbot mode | `quit` |

### Natural Language Commands:

You can also type naturally:

```
🗣️  You: Add a team meeting tomorrow at 3pm for 1 hour

🤖 Assistant: ✅ Created: team meeting on 2025-12-08 15:00-16:00
```

```
🗣️  You: Move calculus to Friday at 10am

   🔍 Found 2 events matching 'calculus':
   [1] Calculus (lecture) - 2025-12-08 08:15
   [2] Calculus - Study - 2025-12-15 10:00
   
   Select event (1-2): 1

🤖 Assistant: ✅ Rescheduled: Calculus (lecture) to 2025-12-12 10:00-12:00
```

```
🗣️  You: Cancel the Python class

🤖 Assistant: ✅ Event cancelled
```

### Date Queries:

```
🗣️  You: What's on my calendar this Friday?

🤖 Assistant: 📅 Events on Friday, December 12, 2025:
   1. Calculus (lecture)
      ⏰ 10:00-12:00 | 📍 Room A101
   2. Lunch Meeting
      ⏰ 12:30-13:30
```

```
🗣️  You: Show me this week's schedule

🤖 Assistant: 📅 Events this week (2025-12-07 to 2025-12-13):
   ...
```

---

## File Upload

### Supported Formats:

| Format | Extension | Notes |
|--------|-----------|-------|
| Images | `.png`, `.jpg`, `.jpeg` | Best for scanned schedules |
| PDF | `.pdf` | Extracts text and/or images |
| Word | `.docx` | Parses text content |

### Tips for Best Results:

1. **Clear Images**: Use high-resolution images with good lighting
2. **Table Format**: Schedule tables are easier to parse than free-form text
3. **Consistent Format**: Include date, time, course name, and location

### Example Upload:

```
🗣️  You: upload

   📁 Supported formats: PNG, JPG, PDF, DOCX
   Enter file path (or 'cancel' to cancel): /Users/me/schedule.png

   🔍 Parsing with AI vision...
   ✅ Found 8 events

   Preview:
   1. Mathematics - 2025-12-09 08:15-10:15
   2. Physics Lab - 2025-12-09 13:30-15:30
   ...

   Sync to Google Calendar? (y/n): y
   ✅ 8 events created
```

---

## Event Search

### Keyword Search:

The system searches Google Calendar for events matching your keyword:

```
🗣️  You: search meeting

🤖 Assistant: 🔍 Found 3 events matching 'meeting':
   1. Team Meeting - 2025-12-08 14:00
   2. Project Meeting - 2025-12-10 10:00
   3. Client Meeting - 2025-12-12 15:00
```

### Partial Name Matching:

When modifying events, partial names work:

```
🗣️  You: move calculus to friday

   🔍 Found 2 events matching 'calculus':
   [1] Calculus (lecture) - 2025-12-08 08:15
   [2] Calculus Tutorial - 2025-12-10 14:00
   [0] Cancel operation

   Select event (1-2) or 0 to cancel: 1
   ✅ Selected: Calculus (lecture)
```

---

## Conflict Detection

### Automatic Detection:

When rescheduling, the system checks for conflicts:

```
🗣️  You: move physics to monday at 9am

   ⚠️ 1 conflict detected:
   • Time overlap: 'Physics' (09:00-11:00) overlaps with 'Mathematics' (08:15-10:15)

   Do you want to proceed anyway? (y/n): 
```

### Manual Check:

```
🗣️  You: conflicts

🤖 Assistant: ⚠️ Found 2 conflict(s):
   1. Time overlap: 'Meeting' (14:00-15:00) overlaps with 'Call' (14:30-15:30)
   2. Time overlap: 'Lunch' (12:00-13:00) overlaps with 'Seminar' (12:30-14:00)
```

---

## Free Slot Finder

```
🗣️  You: free slots

🤖 Assistant: 🕐 Free 1-hour slots (8am - 6pm):

   📅 Monday, Dec 08:
      • 12:30 - 13:30
      • 17:00 - 18:00

   📅 Tuesday, Dec 09:
      • 08:00 - 09:00
      • 15:30 - 18:00
   ...
```

---

## Duplicate Handling

When uploading a schedule, duplicates are detected:

```
   ⚠️ Duplicate found: 'Calculus (lecture)' already exists on 2025-12-08 at 08:15

   What would you like to do?
   [1] Keep existing event (skip this one)
   [2] Replace existing with new
   [3] Keep both events
   [4] Cancel operation

   Your choice (1-4): 
```

---

## Local Cache vs Google Calendar

| Feature | Local Cache | Google Calendar |
|---------|-------------|-----------------|
| **Source** | Uploaded files | Your actual calendar |
| **Persistence** | Temporary (session only) | Permanent |
| **Purpose** | Preview before sync | Final storage |
| **Clear command** | Clears cache only | Not affected |

The `clear` command only clears the local preview cache. Your Google Calendar events remain unchanged.

---

## Example Complete Session

```
============================================================
   🤖 AGENTIC SCHEDULER - CHATBOT MODE
============================================================

🗣️  You: hello

🤖 Assistant: Hello! 👋 I'm your scheduling assistant. What can I do for you?

🗣️  You: upload

   📁 Enter file path: /path/to/schedule.png
   🔍 Parsing...
   ✅ Found 5 events
   Sync to Calendar? (y/n): y
   ✅ 5 events synced

🗣️  You: show me friday

🤖 Assistant: 📅 Events on Friday, December 12:
   1. Calculus - 08:15-10:15
   2. Lab - 13:30-15:30

🗣️  You: move calculus to 10am

   ⚠️ Conflict with 'Lab' detected
   Proceed anyway? (y/n): n
   ❌ Operation cancelled

🗣️  You: move calculus to 3pm

🤖 Assistant: ✅ Rescheduled: Calculus to 2025-12-12 15:00-17:00

🗣️  You: quit

🤖 Assistant: Goodbye! Have a great day! 👋
```

---

## Next Steps

- Check [architecture.md](architecture.md) for system details
- See [api.md](api.md) for API reference
- Review [setup.md](setup.md) if you have configuration issues
