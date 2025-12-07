# Setup Guide for Agentic Scheduler

## Prerequisites

Before setting up the Agentic Scheduler, ensure you have:

- **Python 3.9+** (recommended: 3.11+)
- **pip** (Python package installer)
- **Git** (for cloning the repository)
- **Google Account** (for Google Calendar integration)
- **Azure Account** (for Azure OpenAI API access)

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/Howest_Agentic_AI.git
cd Howest_Agentic_AI/agentic-scheduler
```

---

## Step 2: Create Virtual Environment

It's recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages** (from requirements.txt):
```
openai>=1.0.0
google-auth>=2.0.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
google-api-python-client>=2.0.0
python-dotenv>=1.0.0
PyPDF2>=3.0.0
python-docx>=0.8.11
Pillow>=9.0.0
```

---

## Step 4: Configure Azure OpenAI

### 4.1 Create Azure OpenAI Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new **Azure OpenAI** resource
3. Deploy a **GPT-4** model (with vision capability for image parsing)
4. Note down:
   - Endpoint URL
   - API Key
   - Deployment Name

### 4.2 Create Environment File

Create a `.env` file in the `agentic-scheduler` directory:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
OPENAI_MODEL_NAME=gpt-4o
OPENAI_DEPLOYMENT_NAME=gpt-4o
OPENAI_VERSION_NAME=2025-03-01-preview

# Application Settings
TIMEZONE=Europe/Brussels
LOG_LEVEL=DEBUG
DEBUG_MODE=True
```

---

## Step 5: Configure Google Calendar API

### 5.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable the **Google Calendar API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

### 5.2 Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Desktop app" as application type
4. Name it "Agentic Scheduler"
5. Download the JSON file

### 5.3 Save Credentials

1. Rename the downloaded file to `credentials.json`
2. Place it in the `agentic-scheduler` directory

```
agentic-scheduler/
├── credentials.json    ← Place here
├── src/
├── .env
└── ...
```

### 5.4 Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" user type
3. Fill in required fields:
   - App name: "Agentic Scheduler"
   - User support email: your email
   - Developer contact: your email
4. Add scopes:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`
5. Add your email as a test user

---

## Step 6: First Run Authentication

When you run the application for the first time:

```bash
python src/main.py
```

1. A browser window will open asking you to sign in to Google
2. Select your Google account
3. Grant calendar permissions to the application
4. The `token.json` file will be created automatically

**Note**: The `token.json` file stores your authentication. Keep it secure and don't commit it to version control.

---

## Step 7: Verify Setup

Run the application:

```bash
python src/main.py
```

You should see:

```
============================================================
   📅 AGENTIC SCHEDULER
   Intelligent Schedule Management System
============================================================

   Select Mode:

   [1] 📝 CLI Mode - Step-by-step guided workflow
   [2] 🤖 Chatbot Mode - Natural conversation interface
   [3] ❌ Exit

   Enter your choice (1/2/3):
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Issue: "Google Calendar authentication failed"
1. Delete `token.json` if it exists
2. Ensure `credentials.json` is in the correct location
3. Re-run the application to trigger re-authentication

### Issue: "Azure OpenAI API error"
1. Verify your API key and endpoint in `.env`
2. Ensure your Azure OpenAI deployment is active
3. Check that you have sufficient API quota

### Issue: "Permission denied for calendar"
1. Go to [Google Account Permissions](https://myaccount.google.com/permissions)
2. Remove "Agentic Scheduler" access
3. Re-run the application and re-authenticate

---

## Security Notes

**Never commit these files to version control:**
- `.env` (contains API keys)
- `credentials.json` (contains OAuth secrets)
- `token.json` (contains authentication tokens)

Ensure your `.gitignore` includes:
```
.env
credentials.json
token.json
token.pickle
__pycache__/
*.pyc
venv/
```

---

## Next Steps

- Read [usage.md](usage.md) for detailed usage instructions
- Read [architecture.md](architecture.md) for system architecture
- Check [api.md](api.md) for API reference
