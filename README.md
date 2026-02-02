# 🖥️ Agentic Computer

**Control your Mac computer through WhatsApp messages using AI!**

## Features

- 🔋 **System Controls** - Battery, volume, brightness, lock, shutdown
- 📱 **App Management** - Open, close, and list running applications  
- 📁 **File Operations** - Find files, screenshots, disk space
- 🌐 **Browser Control** - Open URLs, Google/YouTube search
- 🤖 **AI-Powered** - Natural language understanding via Groq

## Quick Start

### 1. Set up API Keys

Edit `config.py` with your credentials:

```python
# Get from https://console.groq.com/keys
GROQ_API_KEY = "your-groq-api-key"

# Get from https://developers.facebook.com/
WA_TOKEN = "your-whatsapp-token"
PHONE_NUMBER_ID = "your-phone-number-id"
```

### 2. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python app.py
```

### 4. Expose with ngrok

```bash
ngrok http 5002
```

Copy the ngrok URL and add `/webhook` to your Meta WhatsApp webhook settings.

## Sample Commands

| Say This | What Happens |
|----------|--------------|
| "battery" | Shows battery percentage |
| "open chrome" | Launches Chrome |
| "close spotify" | Closes Spotify |
| "what apps are running" | Lists open apps |
| "screenshot" | Takes and sends screenshot |
| "find resume.pdf" | Searches for file |
| "open youtube.com" | Opens URL |
| "search google for weather" | Google search |
| "volume 50" | Sets volume to 50% |
| "lock" | Locks the screen |
| "disk space" | Shows storage info |

## Project Structure

```
Agentic Computer/
├── app.py              # Main Flask server
├── config.py           # API keys and settings
├── requirements.txt    # Dependencies
├── controllers/
│   ├── system_controller.py   # System commands
│   ├── app_controller.py      # App management
│   ├── file_controller.py     # File operations
│   └── browser_controller.py  # Browser control
├── ai/
│   └── intent_parser.py       # Groq AI command parser
└── utils/
    └── whatsapp.py            # WhatsApp messaging
```

## Security Note

⚠️ This bot has system-level access. Only run on your personal machine and keep API keys secure!
