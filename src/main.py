# filepath: /agentic-scheduler/agentic-scheduler/src/main.py
"""
Agentic Scheduler - Main Entry Point
Interactive workflow: Upload Schedule → Parse → Conflict Check → Calendar → Change Management
Supports both CLI mode and Chatbot mode
"""
import sys
import os

# Add src directory to Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.parsing_agent import ParsingAgent
from agents.calendar_agent import CalendarAgent
from agents.conflict_evaluation_agent import ConflictEvaluationAgent
from agents.change_management_agent import ChangeManagementAgent
from agents.collaboration_agent import CollaborationAgent
from models.schedule_item import ScheduleItem, EventType


def get_file_path_from_user() -> str:
    """
    Prompt user to enter the path to their schedule file.
    Supports: PDF, DOCX, PNG, JPG, JPEG
    """
    print("\n" + "=" * 60)
    print("📁 Upload Your Schedule")
    print("=" * 60)
    print("\n   Supported file formats:")
    print("   • Images: PNG, JPG, JPEG (photos of schedules)")
    print("   • Documents: PDF, DOCX (digital schedules)")
    print("\n   💡 Tip: You can drag and drop the file into the terminal")
    print("          or paste the full file path.\n")
    
    while True:
        print("   Enter the path to your schedule file (or 'q' to quit): ", end="")
        try:
            file_path = input().strip()
        except EOFError:
            return None
        
        # Handle quit
        if file_path.lower() in ['q', 'quit', 'exit']:
            return None
        
        # Remove quotes if user dragged file (common on macOS)
        file_path = file_path.strip('"').strip("'")
        
        # Expand user home directory
        file_path = os.path.expanduser(file_path)
        
        # Validate file exists
        if not os.path.exists(file_path):
            print(f"\n   ❌ File not found: {file_path}")
            print("   Please check the path and try again.\n")
            continue
        
        # Validate file extension
        valid_extensions = ['.pdf', '.docx', '.png', '.jpg', '.jpeg']
        _, ext = os.path.splitext(file_path.lower())
        
        if ext not in valid_extensions:
            print(f"\n   ❌ Unsupported file type: {ext}")
            print(f"   Supported types: {', '.join(valid_extensions)}\n")
            continue
        
        return file_path


def parse_schedule_file(parsing_agent: ParsingAgent, file_path: str) -> list:
    """
    Parse schedule from the uploaded file.
    """
    _, ext = os.path.splitext(file_path.lower())
    
    print(f"\n   📄 File: {os.path.basename(file_path)}")
    print(f"   📂 Type: {ext.upper()}")
    print(f"\n   🔄 Parsing schedule with AI...")
    
    if ext in ['.png', '.jpg', '.jpeg']:
        # Parse image
        events = parsing_agent.extract_schedule_from_image(file_path)
    elif ext == '.pdf':
        # Parse PDF
        events = parsing_agent.extract_schedule_from_pdf(file_path)
    elif ext == '.docx':
        # Parse DOCX
        events = parsing_agent.extract_schedule_from_docx(file_path)
    else:
        events = None
    
    return events


def display_parsed_events(events: list) -> None:
    """Display the parsed events in a formatted table."""
    if not events:
        return
    
    print(f"\n   ✅ Successfully extracted {len(events)} events:")
    print("\n   " + "-" * 70)
    print(f"   {'#':<3} {'Event':<25} {'Date':<12} {'Time':<13} {'Location':<15}")
    print("   " + "-" * 70)
    
    for i, event in enumerate(events, 1):
        course = event.course[:23] + ".." if len(event.course) > 25 else event.course
        location = (event.location or "N/A")[:13] + ".." if len(event.location or "") > 15 else (event.location or "N/A")
        time_str = f"{event.start_time}-{event.end_time}"
        print(f"   {i:<3} {course:<25} {event.date:<12} {time_str:<13} {location:<15}")
    
    print("   " + "-" * 70)


def confirm_events(events: list) -> bool:
    """Ask user to confirm the parsed events."""
    print("\n   Do these events look correct? (y/n): ", end="")
    try:
        response = input().strip().lower()
        return response in ['y', 'yes']
    except EOFError:
        return True


def interactive_change_management(change_agent: ChangeManagementAgent) -> None:
    """
    Interactive loop for natural language change requests.
    """
    print("\n" + "=" * 60)
    print("✏️ Change Management")
    print("=" * 60)
    print("\n   You can now make changes to your schedule using natural language.")
    print("   Examples:")
    print("   • 'Move Python class to Tuesday at 10:00'")
    print("   • 'Cancel the meeting on Friday'")
    print("   • 'Add a study session on 2025-12-15 from 14:00 to 16:00'")
    print("   • 'Reschedule Math lecture to next week'")
    print("\n   Type 'done' when finished, 'show' to see schedule, or 'quit' to exit.\n")
    
    while True:
        print("   📝 Your request: ", end="")
        try:
            request = input().strip()
        except EOFError:
            break
        
        if not request:
            continue
        
        if request.lower() in ['done', 'quit', 'exit', 'q']:
            break
        
        if request.lower() == 'show':
            display_current_schedule(change_agent.current_schedule)
            continue
        
        if request.lower() == 'help':
            print("\n   📖 Available commands:")
            print("   • Natural language requests to modify schedule")
            print("   • 'show' - Display current schedule")
            print("   • 'done' - Finish and proceed")
            print("   • 'quit' - Exit the program\n")
            continue
        
        # Process the change request
        result = change_agent.process_and_execute(request)
        print(f"\n   {result.get('message', 'Request processed')}\n")


def display_current_schedule(schedule: list) -> None:
    """Display the current schedule grouped by date."""
    if not schedule:
        print("\n   📋 No events in schedule.\n")
        return
    
    print("\n   📋 Current Schedule:")
    print("   " + "-" * 50)
    
    # Group by date
    by_date = {}
    for event in schedule:
        if event.date not in by_date:
            by_date[event.date] = []
        by_date[event.date].append(event)
    
    for date in sorted(by_date.keys()):
        print(f"\n   📅 {date}:")
        for event in sorted(by_date[date], key=lambda x: x.start_time):
            print(f"      • {event.start_time}-{event.end_time}: {event.course}")
            if event.location:
                print(f"        📍 {event.location}")
    
    print("\n   " + "-" * 50 + "\n")


def sync_to_google_calendar(calendar_agent: CalendarAgent, events: list) -> list:
    """
    Sync events to Google Calendar with user confirmation.
    """
    print("\n" + "=" * 60)
    print("📆 Google Calendar Sync")
    print("=" * 60)
    
    print("\n   Would you like to add these events to Google Calendar? (y/n): ", end="")
    try:
        response = input().strip().lower()
    except EOFError:
        response = 'n'
    
    if response not in ['y', 'yes']:
        print("   ℹ️ Skipping Google Calendar sync.")
        return []
    
    print("\n   🔐 Authenticating with Google Calendar...")
    if not calendar_agent.authenticate():
        print("   ❌ Failed to authenticate. Please check credentials.json")
        return []
    
    print("   ✅ Authenticated successfully!")
    print(f"\n   📅 Adding {len(events)} events to Google Calendar...")
    print("   (You may be prompted if duplicates are found)\n")
    
    created_ids = calendar_agent.create_events_batch(events)
    
    return created_ids


def main():
    print("\n" + "=" * 60)
    print("   📅 AGENTIC SCHEDULER")
    print("   Intelligent Schedule Management System")
    print("=" * 60)
    
    # =========================================================
    # STEP 1: Initialize all agents
    # =========================================================
    print("\n🔧 Initializing AI agents...")
    
    parsing_agent = ParsingAgent()
    calendar_agent = CalendarAgent()
    conflict_agent = ConflictEvaluationAgent()
    change_agent = ChangeManagementAgent()
    collaboration_agent = CollaborationAgent()
    
    # Wire up the agents
    change_agent.set_calendar_agent(calendar_agent)
    change_agent.set_conflict_agent(conflict_agent)
    collaboration_agent.set_agents(calendar_agent, change_agent, conflict_agent)
    
    print("   ✅ All agents ready!")
    
    # =========================================================
    # STEP 2: Get schedule file from user
    # =========================================================
    file_path = get_file_path_from_user()
    
    if not file_path:
        print("\n   👋 Goodbye!")
        return
    
    # =========================================================
    # STEP 3: Parse the schedule
    # =========================================================
    print("\n" + "=" * 60)
    print("📝 Parsing Your Schedule")
    print("=" * 60)
    
    events = parse_schedule_file(parsing_agent, file_path)
    
    if not events:
        print("\n   ❌ Failed to extract events from the file.")
        print("   Please ensure the file contains a readable schedule.")
        return
    
    display_parsed_events(events)
    
    if not confirm_events(events):
        print("\n   ℹ️ You can manually edit events during change management.")
    
    # Set schedule context for agents
    change_agent.set_schedule(events)
    conflict_agent.set_events(events)
    
    # =========================================================
    # STEP 4: Check for conflicts
    # =========================================================
    print("\n" + "=" * 60)
    print("🔍 Analyzing Schedule for Conflicts")
    print("=" * 60)
    
    conflicts = conflict_agent.check_conflicts(events)
    
    if conflicts:
        print(f"\n   ⚠️ Found {len(conflicts)} conflict(s):")
        for i, conflict in enumerate(conflicts, 1):
            severity_icon = "🔴" if conflict.severity == "high" else "🟡"
            print(f"\n   {i}. {severity_icon} {conflict.message}")
            
            # Get AI resolution suggestion
            print("      💡 Getting AI suggestion...")
            suggestion = conflict_agent.get_ai_resolution(conflict)
            if suggestion:
                # Truncate long suggestions
                suggestion_display = suggestion[:150] + "..." if len(suggestion) > 150 else suggestion
                print(f"      💡 {suggestion_display}")
    else:
        print("\n   ✅ No conflicts detected! Your schedule looks good.")
    
    # =========================================================
    # STEP 5: Interactive change management
    # =========================================================
    interactive_change_management(change_agent)
    
    # =========================================================
    # STEP 6: Show final schedule
    # =========================================================
    print("\n" + "=" * 60)
    print("📋 Final Schedule")
    print("=" * 60)
    
    display_current_schedule(change_agent.current_schedule)
    
    # =========================================================
    # STEP 7: Sync to Google Calendar
    # =========================================================
    updated_events = change_agent.current_schedule
    
    if updated_events:
        created_ids = sync_to_google_calendar(calendar_agent, updated_events)
        
        if created_ids:
            print(f"\n   ✅ Successfully synced {len(created_ids)} events to Google Calendar!")
    
    # =========================================================
    # STEP 8: Find free slots
    # =========================================================
    print("\n" + "=" * 60)
    print("🕐 Available Free Time Slots")
    print("=" * 60)
    
    # Get unique dates from schedule
    dates = sorted(set(e.date for e in updated_events)) if updated_events else []
    
    if dates:
        for date in dates[:3]:  # Check first 3 days
            free_slots = conflict_agent.find_free_slots(updated_events, date, duration_minutes=60)
            print(f"\n   📅 {date} - Free 1-hour slots:")
            if free_slots:
                for start, end in free_slots[:5]:  # Show max 5 slots
                    print(f"      • {start} - {end}")
            else:
                print("      • No free slots available")
    else:
        print("\n   ℹ️ No events in schedule to analyze.")
    
    # =========================================================
    # Summary
    # =========================================================
    print("\n" + "=" * 60)
    print("✨ Session Complete!")
    print("=" * 60)
    print(f"""
   Summary:
   • Events parsed: {len(events) if events else 0}
   • Final events: {len(updated_events) if updated_events else 0}
   • Conflicts found: {len(conflicts) if conflicts else 0}
   
   Thank you for using Agentic Scheduler!
   """)


def chatbot_mode():
    """
    Interactive chatbot mode for the Agentic Scheduler.
    Allows natural conversation with the scheduling assistant.
    """
    print("\n" + "=" * 60)
    print("   🤖 AGENTIC SCHEDULER - CHATBOT MODE")
    print("   Your Intelligent Scheduling Assistant")
    print("=" * 60)
    
    # Initialize agents
    print("\n🔧 Initializing AI agents...")
    
    parsing_agent = ParsingAgent()
    calendar_agent = CalendarAgent()
    conflict_agent = ConflictEvaluationAgent()
    change_agent = ChangeManagementAgent()
    
    # Wire up the agents
    change_agent.set_calendar_agent(calendar_agent)
    change_agent.set_conflict_agent(conflict_agent)
    
    # Authenticate with Google Calendar
    print("🔐 Connecting to Google Calendar...")
    if calendar_agent.authenticate():
        print("   ✅ Connected to Google Calendar!")
    else:
        print("   ⚠️ Google Calendar not connected. Some features may be limited.")
    
    print("\n   ✅ All agents ready!")
    
    # Display help
    print("\n" + "-" * 60)
    print("💬 CHATBOT COMMANDS:")
    print("-" * 60)
    print("""
   📁 FILE COMMANDS:
      • 'upload' or 'parse' - Upload a schedule file (PDF, DOCX, PNG, JPG)
      • 'show' or 'schedule' - Display current schedule
      • 'events' - List upcoming Google Calendar events
   
   ✏️ SCHEDULING COMMANDS (Natural Language):
      • 'Add a meeting tomorrow at 2pm'
      • 'Schedule Python class on Monday from 9:00 to 10:30'
      • 'Move the meeting to Friday'
      • 'Cancel the workshop'
      • 'What's on my calendar this week?'
   
   🔍 ANALYSIS COMMANDS:
      • 'conflicts' - Check for scheduling conflicts
      • 'free slots' or 'free time' - Find available time slots
   
   ℹ️ OTHER:
      • 'help' - Show this help message
      • 'clear' - Clear local cache (does NOT delete Google Calendar events)
      • 'quit' or 'exit' - Exit chatbot mode
   """)
    print("-" * 60)
    
    # Conversation state
    current_schedule = []
    conversation_history = []
    
    while True:
        try:
            print("\n🗣️  You: ", end="")
            user_input = input().strip()
            
            if not user_input:
                continue
            
            # Store in conversation history
            conversation_history.append(f"User: {user_input}")
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\n🤖 Assistant: Goodbye! Have a great day! 👋")
                break
            
            # Process commands
            response = process_chatbot_command(
                user_input, 
                parsing_agent, 
                calendar_agent, 
                conflict_agent, 
                change_agent,
                current_schedule
            )
            
            # Update schedule if changed
            if change_agent.current_schedule:
                current_schedule = change_agent.current_schedule
            
            # Display response
            print(f"\n🤖 Assistant: {response}")
            
            # Store in conversation history
            conversation_history.append(f"Assistant: {response}")
            
        except KeyboardInterrupt:
            print("\n\n🤖 Assistant: Chat interrupted. Goodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("   Please try again or type 'help' for commands.")


def process_chatbot_command(user_input: str, parsing_agent, calendar_agent, 
                           conflict_agent, change_agent, current_schedule) -> str:
    """
    Process user input and return appropriate response.
    """
    input_lower = user_input.lower().strip()
    
    # Greetings
    if input_lower in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']:
        return """Hello! 👋 I'm your scheduling assistant. I can help you:

• 📁 Parse schedules from images/PDFs (type 'upload')
• 📅 Add/modify/cancel events using natural language
• 🔍 Check for conflicts and find free time slots
• 📆 View your Google Calendar events
• 🔎 Search events by keyword (type 'search [keyword]')

What would you like to do?"""
    
    # How are you / small talk
    if any(phrase in input_lower for phrase in ['how are you', 'how r u', "what's up", 'whats up']):
        return "I'm doing great, thanks for asking! 😊 Ready to help with your scheduling needs. What can I do for you today?"
    
    # Help command
    if input_lower == 'help':
        return """Here are the available commands:

📁 Upload a schedule: Type 'upload' or 'parse'
📋 Show schedule: Type 'show' or 'schedule'
📅 List calendar events: Type 'events'
🔎 Search events: Type 'search [keyword]' (e.g., 'search calculus')
🔍 Check conflicts: Type 'conflicts'
🕐 Find free time: Type 'free slots' or 'free time'
🗑️ Clear local cache: Type 'clear' (does NOT delete Google Calendar events)

Or just type naturally:
• 'Add a team meeting tomorrow at 3pm for 1 hour'
• 'Schedule lunch on Friday from 12:00 to 13:00'
• 'Move calculus to next Monday at 2pm'
• 'Cancel the Python class'"""
    
    # Search command - NEW!
    if input_lower.startswith('search ') or input_lower.startswith('find '):
        keyword = user_input.split(' ', 1)[1] if ' ' in user_input else ''
        if keyword:
            return handle_search_events(calendar_agent, keyword)
        return "🔎 Please specify a keyword to search, e.g., 'search calculus'"
    
    # Upload/Parse command
    if input_lower in ['upload', 'parse', 'load', 'import']:
        return handle_file_upload(parsing_agent, change_agent, conflict_agent)
    
    # Show schedule command
    if input_lower in ['show', 'schedule', 'list', 'my schedule']:
        return format_schedule_for_chat(change_agent.current_schedule or current_schedule)
    
    # List Google Calendar events
    if input_lower in ['events', 'calendar', 'google calendar', 'upcoming']:
        return handle_list_events(calendar_agent)
    
    # Check conflicts
    if input_lower in ['conflicts', 'check conflicts', 'overlaps']:
        # First try local schedule, then fall back to Google Calendar
        schedule = change_agent.current_schedule or current_schedule
        if not schedule:
            # Get events from Google Calendar for the next 7 days
            from datetime import datetime, timedelta
            today = datetime.now()
            start_date = today.strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
            schedule = calendar_agent.get_events(start_date, end_date)
            if not schedule:
                return "📅 No events found in Google Calendar for the next 7 days."
        
        conflicts = conflict_agent.check_conflicts(schedule)
        if conflicts:
            result = f"⚠️ Found {len(conflicts)} conflict(s):\n"
            for i, c in enumerate(conflicts, 1):
                result += f"   {i}. {c.message}\n"
            return result
        return "✅ No conflicts found in your schedule!"
    
    # Find free slots
    if 'free' in input_lower and ('slot' in input_lower or 'time' in input_lower):
        # First try local schedule, then fall back to Google Calendar
        schedule = change_agent.current_schedule or current_schedule
        if not schedule:
            # Get events from Google Calendar for the next 7 days
            from datetime import datetime, timedelta
            today = datetime.now()
            start_date = today.strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
            schedule = calendar_agent.get_events(start_date, end_date)
            if not schedule:
                return "📅 No events found in Google Calendar for the next 7 days."
        return handle_free_slots(conflict_agent, schedule)
    
    # Clear schedule
    if input_lower in ['clear', 'reset', 'new']:
        change_agent.set_schedule([])
        return "🗑️ Local schedule cache cleared!\n\n📝 Note: This only clears the locally loaded schedule (from uploaded files).\n   Your Google Calendar events are NOT affected.\n   Use 'events' to see your Google Calendar events."
    
    # Date-specific event listing (e.g., "list friday", "what's on monday", "show friday events")
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 
                 'today', 'tomorrow', 'this week']
    if any(day in input_lower for day in day_names):
        # Check if it's asking about events on a specific day
        if any(keyword in input_lower for keyword in ['list', 'show', 'what', 'events', 'appointments', 
                                                       'meetings', 'schedule', 'my', 'on', 'for']):
            # Extract the day from the input
            for day in day_names:
                if day in input_lower:
                    return handle_list_events_by_date(calendar_agent, day)
    
    # Questions about calendar
    if any(keyword in input_lower for keyword in ["what's on", "what is on", "when", "do i have", 
                                                   "am i", "show me my", "tell me my", "my events",
                                                   "my calendar", "my meetings"]):
        return handle_list_events(calendar_agent)
    
    # Natural language processing for schedule changes
    # This handles: add, schedule, move, cancel, reschedule, etc.
    if any(keyword in input_lower for keyword in ['add', 'schedule', 'create', 'book', 'move', 
                                                   'cancel', 'delete', 'remove', 'reschedule',
                                                   'change', 'modify', 'update', 'set up']):
        return handle_natural_language_request(change_agent, user_input)
    
    # Thank you
    if any(phrase in input_lower for phrase in ['thank', 'thanks', 'thx']):
        return "You're welcome! 😊 Let me know if you need anything else."
    
    # Default: provide helpful guidance
    return f"""I'm not sure how to help with that. Here's what I can do:

📁 'upload' - Parse a schedule file
📅 'events' - Show your calendar
🔎 'search [keyword]' - Search events by keyword
✏️ Use natural language like:
   • 'Add meeting tomorrow at 2pm'
   • 'Move calculus to Friday at 10am'

Type 'help' for more commands!"""


def handle_file_upload(parsing_agent, change_agent, conflict_agent) -> str:
    """Handle file upload in chatbot mode."""
    print("\n   📁 Supported formats: PNG, JPG, PDF, DOCX")
    print("   Enter file path (or 'cancel' to cancel): ", end="")
    
    try:
        file_path = input().strip().strip('"').strip("'")
    except EOFError:
        return "❌ File upload cancelled."
    
    if file_path.lower() == 'cancel':
        return "❌ File upload cancelled."
    
    file_path = os.path.expanduser(file_path)
    
    if not os.path.exists(file_path):
        return f"❌ File not found: {file_path}"
    
    _, ext = os.path.splitext(file_path.lower())
    valid_extensions = ['.pdf', '.docx', '.png', '.jpg', '.jpeg']
    
    if ext not in valid_extensions:
        return f"❌ Unsupported file type: {ext}. Supported: {', '.join(valid_extensions)}"
    
    print(f"\n   🔄 Parsing {os.path.basename(file_path)}...")
    
    if ext in ['.png', '.jpg', '.jpeg']:
        events = parsing_agent.extract_schedule_from_image(file_path)
    elif ext == '.pdf':
        events = parsing_agent.extract_schedule_from_pdf(file_path)
    elif ext == '.docx':
        events = parsing_agent.extract_schedule_from_docx(file_path)
    else:
        events = None
    
    if not events:
        return "❌ Could not extract events from the file. Please try a different file."
    
    # Set schedule in change agent
    change_agent.set_schedule(events)
    conflict_agent.set_events(events)
    
    # Format response
    result = f"✅ Successfully extracted {len(events)} events!\n\n"
    result += format_schedule_for_chat(events)
    
    # Check for conflicts
    conflicts = conflict_agent.check_conflicts(events)
    if conflicts:
        result += f"\n\n⚠️ Note: {len(conflicts)} conflict(s) detected. Type 'conflicts' for details."
    
    return result


def handle_search_events(calendar_agent, keyword: str) -> str:
    """Search Google Calendar events by keyword."""
    try:
        matches = calendar_agent.search_events_by_keyword(keyword)
        
        if not matches:
            return f"🔎 No events found matching '{keyword}'.\n\n💡 Try a different keyword or type 'events' to see all upcoming events."
        
        result = f"🔎 Found {len(matches)} event(s) matching '{keyword}':\n"
        result += "-" * 50 + "\n"
        
        for i, event in enumerate(matches[:10], 1):  # Limit to 10
            result += f"\n   [{i}] {event.course}\n"
            result += f"       📅 {event.date} | ⏰ {event.start_time}-{event.end_time}\n"
            if event.location:
                result += f"       📍 {event.location}\n"
        
        result += "\n" + "-" * 50
        result += "\n\n💡 You can now use these events in commands like:"
        result += f"\n   • 'Move {matches[0].course[:20]}... to Friday at 2pm'"
        result += f"\n   • 'Cancel {matches[0].course[:20]}...'"
        
        return result
        
    except Exception as e:
        return f"❌ Could not search events: {e}"


def handle_list_events_by_date(calendar_agent, date_str: str) -> str:
    """List events for a specific date from Google Calendar."""
    try:
        from datetime import datetime, timedelta
        
        # Parse various date formats
        date_lower = date_str.lower().strip()
        today = datetime.now()
        target_date = None
        
        # Handle day names
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(day_names):
            if day in date_lower:
                # Find next occurrence of this day
                days_ahead = i - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                break
        
        # Handle relative dates
        if target_date is None:
            if 'today' in date_lower:
                target_date = today
            elif 'tomorrow' in date_lower:
                target_date = today + timedelta(days=1)
            elif 'this week' in date_lower:
                # Get all events for this week
                start_date = today.strftime('%Y-%m-%d')
                end_of_week = today + timedelta(days=(6 - today.weekday()))
                end_date = end_of_week.strftime('%Y-%m-%d')
                events = calendar_agent.get_events(start_date, end_date)
                
                if not events:
                    return f"📅 No events found this week."
                
                result = f"📅 Events this week ({start_date} to {end_date}):\n"
                result += "-" * 40 + "\n"
                
                for i, event in enumerate(events, 1):
                    result += f"   {i}. {event.course}\n"
                    result += f"      📅 {event.date} {event.start_time}-{event.end_time}"
                    if event.location:
                        result += f" | 📍 {event.location}"
                    result += "\n"
                
                return result
        
        # If we have a target date
        if target_date:
            date_formatted = target_date.strftime('%Y-%m-%d')
            events = calendar_agent.get_events(date_formatted, date_formatted)
            
            if not events:
                return f"📅 No events found on {target_date.strftime('%A, %B %d')}."
            
            result = f"📅 Events on {target_date.strftime('%A, %B %d, %Y')}:\n"
            result += "-" * 40 + "\n"
            
            for i, event in enumerate(events, 1):
                result += f"   {i}. {event.course}\n"
                result += f"      ⏰ {event.start_time}-{event.end_time}"
                if event.location:
                    result += f" | 📍 {event.location}"
                result += "\n"
            
            return result
        
        return f"📅 Could not understand the date '{date_str}'. Try 'events on friday' or 'events today'."
        
    except Exception as e:
        return f"❌ Could not fetch events: {e}"


def handle_list_events(calendar_agent) -> str:
    """List upcoming events from Google Calendar."""
    try:
        # Use list_upcoming_events which returns ScheduleItem objects
        events = calendar_agent.list_upcoming_events(max_results=10)
        
        if not events:
            return "📅 No upcoming events found in Google Calendar."
        
        result = f"📅 Your next {len(events)} events:\n"
        result += "-" * 40 + "\n"
        
        for i, event in enumerate(events, 1):
            result += f"   {i}. {event.course}\n"
            result += f"      📅 {event.date} {event.start_time}-{event.end_time}"
            if event.location:
                result += f" | 📍 {event.location}"
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"❌ Could not fetch events: {e}"


def handle_free_slots(conflict_agent, schedule) -> str:
    """Find and display free time slots."""
    if not schedule:
        return "📋 No events to analyze."
    
    # Get unique dates from the schedule
    dates = sorted(set(e.date for e in schedule))
    
    if not dates:
        return "📋 No dates in schedule to analyze."
    
    # Also include the next 5 days even if no events
    from datetime import datetime, timedelta
    today = datetime.now()
    for i in range(5):
        date_str = (today + timedelta(days=i)).strftime('%Y-%m-%d')
        if date_str not in dates:
            dates.append(date_str)
    dates = sorted(dates)[:7]  # Limit to 7 days
    
    result = "🕐 Free 1-hour slots (8am - 6pm):\n"
    
    for date in dates:
        free_slots = conflict_agent.find_free_slots(schedule, date, duration_minutes=60)
        
        # Format the date nicely
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%A, %b %d')
        except:
            date_formatted = date
            
        result += f"\n   📅 {date_formatted}:\n"
        if free_slots:
            for start, end in free_slots[:4]:  # Show max 4 slots per day
                result += f"      • {start} - {end}\n"
        else:
            result += "      • No free slots (fully booked)\n"
    
    return result


def handle_natural_language_request(change_agent, user_input: str) -> str:
    """Process natural language scheduling requests."""
    try:
        # Check if the request has enough detail for adding an event
        input_lower = user_input.lower()
        
        # If adding an event without end time, suggest adding it
        if any(word in input_lower for word in ['add', 'create', 'schedule', 'book']):
            # Check if end time might be missing
            has_duration = any(word in input_lower for word in ['hour', 'minute', 'min', 'hr', 'for 1', 'for 2', 'for 30'])
            has_time_range = '-' in user_input or ' to ' in input_lower or 'until' in input_lower
            
            if not has_duration and not has_time_range:
                # Assume 1 hour default duration
                print("   💡 No end time specified. Assuming 1 hour duration.")
        
        result = change_agent.process_and_execute(user_input, auto_confirm=False)
        message = result.get('message', 'Request processed.')
        
        # Check if event not found - might need to search Google Calendar
        if "Event not found" in message or "No events in schedule" in message:
            # Extract potential event name from user input for move/cancel/reschedule
            if any(word in input_lower for word in ['move', 'cancel', 'delete', 'reschedule', 'remove']):
                # Try to extract the event name keyword
                keywords = ['move', 'cancel', 'delete', 'reschedule', 'remove', 'the', 'event', 'meeting', 'class', 'to', 'on', 'at', 'from']
                words = input_lower.split()
                potential_keywords = [w for w in words if w not in keywords and len(w) > 2]
                
                if potential_keywords and change_agent.calendar_agent:
                    # Search Google Calendar with extracted keywords
                    for keyword in potential_keywords[:2]:  # Try first 2 potential keywords
                        matches = change_agent.calendar_agent.search_events_by_keyword(keyword)
                        if matches:
                            # Found matches! Show them and let _search_calendar_with_selection handle it
                            return handle_search_and_select_for_action(change_agent, keyword, user_input, matches)
        
        return message
            
    except Exception as e:
        return f"""❌ Could not process that request.

💡 Try being more specific with dates and times:
   • 'Add dentist appointment on 2025-12-12 from 12:30 to 13:30'
   • 'Schedule meeting tomorrow from 14:00 to 15:00'
   
Error: {e}"""


def handle_search_and_select_for_action(change_agent, keyword: str, original_request: str, matches: list) -> str:
    """
    Show matching events and let user select one for the action.
    """
    print(f"\n   🔍 Found {len(matches)} event(s) matching '{keyword}' in Google Calendar:")
    print("   " + "-" * 50)
    
    for i, event in enumerate(matches[:10], 1):
        print(f"   [{i}] {event.course}")
        print(f"       📅 {event.date} | ⏰ {event.start_time}-{event.end_time}")
        if event.location:
            print(f"       📍 {event.location}")
    
    print("   [0] Cancel operation")
    print("   " + "-" * 50)
    print(f"\n   Select event (1-{min(len(matches), 10)}) or 0 to cancel: ", end="")
    
    try:
        choice = input().strip()
        
        if choice == '0' or choice.lower() == 'cancel':
            return "❌ Operation cancelled."
        
        try:
            index = int(choice) - 1
            if 0 <= index < min(len(matches), 10):
                selected_event = matches[index]
                print(f"   ✅ Selected: {selected_event.course}")
                
                # Add selected event to current schedule so it can be found
                if selected_event not in change_agent.current_schedule:
                    change_agent.current_schedule.append(selected_event)
                
                # Now re-process the original request
                result = change_agent.process_and_execute(original_request, auto_confirm=False)
                return result.get('message', 'Request processed.')
            else:
                return "⚠️ Invalid selection. Operation cancelled."
        except ValueError:
            return "⚠️ Invalid input. Operation cancelled."
            
    except EOFError:
        return "⚠️ Non-interactive mode. Please specify the full event name."


def format_schedule_for_chat(schedule) -> str:
    """Format schedule for chat display."""
    if not schedule:
        return "📋 No events in schedule."
    
    # Group by date
    by_date = {}
    for event in schedule:
        if event.date not in by_date:
            by_date[event.date] = []
        by_date[event.date].append(event)
    
    result = f"📋 Current Schedule ({len(schedule)} events):\n"
    result += "-" * 40 + "\n"
    
    for date in sorted(by_date.keys()):
        result += f"\n📅 {date}:\n"
        for event in sorted(by_date[date], key=lambda x: x.start_time):
            result += f"   • {event.start_time}-{event.end_time}: {event.course}\n"
            if event.location:
                result += f"     📍 {event.location}\n"
    
    return result


def select_mode():
    """Let user select between CLI mode and Chatbot mode."""
    print("\n" + "=" * 60)
    print("   📅 AGENTIC SCHEDULER")
    print("   Intelligent Schedule Management System")
    print("=" * 60)
    print("\n   Select Mode:\n")
    print("   [1] 📝 CLI Mode - Step-by-step guided workflow")
    print("   [2] 🤖 Chatbot Mode - Natural conversation interface")
    print("   [3] ❌ Exit")
    print("\n   Enter your choice (1/2/3): ", end="")
    
    try:
        choice = input().strip()
    except EOFError:
        choice = '3'
    
    return choice


if __name__ == "__main__":
    choice = select_mode()
    
    if choice == '1':
        main()
    elif choice == '2':
        chatbot_mode()
    else:
        print("\n   👋 Goodbye!")