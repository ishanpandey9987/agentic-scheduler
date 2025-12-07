"""
Configuration settings for the Agentic Scheduler
Uses environment variables for sensitive data
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI Settings
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
OPENAI_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME", "gpt-4")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2024-02-15-preview")

# Google Calendar Settings
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

# Legacy API Keys (for backward compatibility)
API_KEYS = {
    "google_calendar": os.getenv("GOOGLE_CALENDAR_API_KEY", ""),
    "icloud": os.getenv("ICLOUD_API_KEY", "")
}

DATABASE_SETTINGS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "agentic_scheduler_db")
}

SCHEDULING_SETTINGS = {
    "default_event_duration": 60,  # in minutes
    "time_zone": os.getenv("TIMEZONE", "Europe/Brussels")
}

LOGGING_SETTINGS = {
    "log_file": "agentic_scheduler.log",
    "log_level": os.getenv("LOG_LEVEL", "DEBUG")
}

# Agent Settings
MAX_RETRIES = 3
TEMPERATURE = 0.1