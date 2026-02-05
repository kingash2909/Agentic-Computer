# 🤖 Agentic Computer - Supported Commands

Your bot is now fully cross-platform (**macOS & Windows**) and supports complete remote control via WhatsApp.

## 🖥️ System Control
| Command | Description | Platform |
| :--- | :--- | :--- |
| `shutdown` | Power off the computer | Both |
| `restart` | Reboot the computer | Both |
| `sleep` | Put computer to sleep | Both |
| `lock screen` | Lock the computer | Both |
| `volume [0-100]` | Set system volume | Both |
| `mute` / `unmute` | Toggle audio | Both |
| `battery` | Check power status | Both |
| `system status` | Detailed CPU, RAM, and Uptime | Both |
| `clipboard` | Get current copied text | Both |
| `brightness [0-100]` | Set screen brightness | Both |

## �️ Remote Access (Pseudo-VNC)
| Command | Description | Example |
| :--- | :--- | :--- |
| `live` / `show view` | Get an instant screenshot | "show me what's happening" |
| `click at [x] [y]`| Click at coordinates | "click at 500 400" |
| `type [text]` | Type text on your computer | "type hello world" |
| `press [key]` | Press a specific key | "press enter", "press esc" |
| `run [command]` | Execute terminal/shell command | "run ls -la on desktop" |
| `screen info` | Get resolution and mouse position | "where is my mouse" |

## 📂 File Management
| Command | Description | Note |
| :--- | :--- | :--- |
| `screenshot` | Capture current screen | Standard capture |
| `find [file]` | Search for a file | Spotlight (Mac) / Dir (Win) |
| `get [path]` | Fetch a file to WhatsApp | Limit: 10MB |
| `list [folder]` | View folder contents | e.g. "list downloads" |
| `disk space` | Check storage usage | Both |

## 📱 Applications
| Command | Description | Example |
| :--- | :--- | :--- |
| `open [app]` | Launch an application | "open chrome", "open notepad" |
| `close [app]` | Quit an app gracefully | "close spotify" |
| `kill [app]` | Force quit an app | "kill chrome" |
| `list apps` | See all active GUI apps | Both |
| `current app` | Get the active foreground app | Both |

## 🌐 Browser & Media
*   **Web**: `open youtube.com`, `google weather`, `search youtube for music`.
*   **Media**: `play`, `pause`, `next song`, `previous track`, `now playing`.

---
> [!TIP]
> Use **"run [shell command]"** for powerful remote administration.
> Use **"live"** followed by **"click"** to navigate your computer visually!
