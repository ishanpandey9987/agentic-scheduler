# Agentic Scheduler

An AI-powered scheduling assistant that converts static schedules into Google Calendar events using multi-agent architecture.

## ✨ Features

- 🖼️ **Vision Parsing** - Extract schedules from images, PDFs, and Word documents
- 📅 **Google Calendar Sync** - Full CRUD with duplicate detection
- 💬 **Natural Language Interface** - Chatbot mode for conversational commands
- ⚠️ **Conflict Detection** - Automatic scheduling overlap detection
- 🔍 **Smart Search** - Find events by partial name

## 🚀 Quick Start

```bash
# 1. Clone and setup
cd agentic-scheduler
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure (see docs/setup.md for full guide)
cp .env.example .env
# Add your Azure OpenAI keys and Google credentials.json

# 3. Run
python src/main.py
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[Setup Guide](docs/SETUP.md)** | Installation, API keys, Google OAuth configuration |
| **[Usage Guide](docs/USAGE.md)** | CLI mode, Chatbot mode, command reference |
| **[Architecture](docs/ARCHITECTURE.md)** | Multi-agent design, data flow, technology stack |
| **[API Reference](docs/API.md)** | Python API for all 5 agents |

## 🏗️ Project Structure

```
agentic-scheduler/
├── src/
│   ├── main.py          # Entry point (CLI & Chatbot modes)
│   ├── agents/          # 5 AI agents
│   ├── models/          # ScheduleItem, Conflict, ChangeRequest
│   └── config/          # Settings and environment
├── tests/               # Unit tests (84 tests)
├── docs/                # Documentation
└── requirements.txt     # Dependencies
```

## 🧪 Testing

```bash
pytest tests/ -v              # Run all tests
pytest tests/ --cov=src       # With coverage
```

## 📄 License

MIT License

