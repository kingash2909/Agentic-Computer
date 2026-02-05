# 🖥️ Agentic Computer

**Control your Mac computer through WhatsApp messages using AI!**

## Features

- 🔋 **System Controls** - Battery, volume, brightness, lock, shutdown
- 📱 **App Management** - Open, close, and list running applications  
- 📁 **File Operations** - Find files, screenshots, disk space
- 🌐 **Browser Control** - Open URLs, Google/YouTube search
- 🤖 **AI-Powered** - Natural language understanding via Groq
- 📸 **Persistent Screenshots** - All screenshots are stored in the local `screenshots/` folder.

## Quick Start

### 1. Set up Environment Variables

Create a `.env` file (based on `.env.example`) with your credentials:

```bash
WA_TOKEN=your-whatsapp-token
PHONE_NUMBER_ID=your-phone-number-id
VERIFY_TOKEN=your-secret-verify-token
GROQ_API_KEY=your-groq-api-key
```

### 2. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Server (The Hub)

```bash
python server/run_server.py
```

### 4. Run the Agent (The Client)

You can run either the CLI version or the GUI version:

**CLI:**
```bash
python agent/run_agent.py
```

**GUI:**
```bash
python agent/gui_app.py
```

### 5. Go Live (Webhook)

Your bot is now fully cross-platform (**macOS & Windows**) and supports complete remote control via WhatsApp.

#### Remote Command Guide
| Command Category | Examples |
| :--- | :--- |
| **System** | `battery`, `volume 50`, `brightness 70`, `lock`, `restart` |
| **Apps** | `open chrome`, `close spotify`, `list apps` |
| **Files** | `screenshot`, `find report.pdf`, `disk space` |
| **Browser** | `google weather`, `open youtube.com`, `search youtube` |
| **Remote Control** | `live`, `click at 500 400`, `type hello`, `press enter` |

#### Deployment Options

**Local Testing (ngrok):**
1. Run `ngrok http 5002`
2. Copy the `https` URL (e.g., `https://xyz.ngrok-free.app`)
3. Set your WhatsApp Webhook URL to `https://xyz.ngrok-free.app/webhook` in the Meta Developer Dashboard.

**Cloud Deployment:**

- **Railway.app (Easiest)**:
  1. Connect your GitHub Repo.
  2. Railway will automatically detect the `Procfile` or `Dockerfile`.
  3. Add your variables in the "Variables" tab.
- **Render.com**:
  1. New -> Web Service -> Connect GitHub Repo.
  2. Set "Start Command" to `gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:$PORT server.run_server:app`.
- **DigitalOcean / AWS / GCP**:
  1. Use the [Dockerfile](file:///Users/ashishmishra/Desktop/Building%20Projects/Agentic%20Computer%20/Dockerfile) to build and deploy a container.

## Project Structure

```
Agentic Computer/
├── agent/               # Client-side logic
│   ├── run_agent.py     # CLI Agent entry
│   ├── gui_app.py       # GUI Agent entry
│   └── core/            # Functional controllers
├── server/              # Server-side logic (The Hub)
│   ├── run_server.py    # Server entry point
│   └── app/             # Services (AI, WhatsApp)
├── screenshots/         # Persistent storage for captures
└── config.py            # Configuration loader
```

## Security Note

⚠️ This bot has system-level access. Only run on your personal machine and keep API keys secure!
