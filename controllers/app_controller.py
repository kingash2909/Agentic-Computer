"""
App Controller - Handles application management
Supports: open, close, list running apps, switch to app
"""

import subprocess
import psutil


# Common app name mappings (what user says -> actual app name)
APP_MAPPINGS = {
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "safari": "Safari",
    "firefox": "Firefox",
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "terminal": "Terminal",
    "iterm": "iTerm",
    "spotify": "Spotify",
    "slack": "Slack",
    "discord": "Discord",
    "zoom": "zoom.us",
    "teams": "Microsoft Teams",
    "finder": "Finder",
    "notes": "Notes",
    "calendar": "Calendar",
    "mail": "Mail",
    "messages": "Messages",
    "whatsapp": "WhatsApp",
    "telegram": "Telegram",
    "notion": "Notion",
    "figma": "Figma",
    "photoshop": "Adobe Photoshop",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "music": "Music",
    "photos": "Photos",
    "preview": "Preview",
    "system preferences": "System Preferences",
    "settings": "System Preferences",
}


def _get_app_name(user_input):
    """Convert user input to actual app name"""
    user_input_lower = user_input.lower().strip()
    return APP_MAPPINGS.get(user_input_lower, user_input)


def open_app(app_name):
    """Open an application"""
    try:
        actual_name = _get_app_name(app_name)
        subprocess.run(["open", "-a", actual_name], check=True)
        return f"✅ Opened {actual_name}"
    except subprocess.CalledProcessError:
        return f"❌ Could not find app: {app_name}. Make sure it's installed."
    except Exception as e:
        return f"❌ Failed to open {app_name}: {str(e)}"


def close_app(app_name):
    """Close an application"""
    try:
        actual_name = _get_app_name(app_name)
        subprocess.run([
            "osascript", "-e",
            f'tell application "{actual_name}" to quit'
        ], check=True)
        return f"✅ Closed {actual_name}"
    except Exception as e:
        return f"❌ Failed to close {app_name}: {str(e)}"


def list_running_apps():
    """List all running GUI applications"""
    try:
        result = subprocess.run([
            "osascript", "-e",
            'tell application "System Events" to get name of every process whose background only is false'
        ], capture_output=True, text=True)
        
        apps = result.stdout.strip().split(", ")
        
        if not apps or apps == ['']:
            return "No apps currently running."
        
        # Filter out system processes
        system_apps = {"Finder", "Dock", "SystemUIServer", "Spotlight", "Control Center"}
        user_apps = [app for app in apps if app not in system_apps]
        
        if not user_apps:
            return "📱 Only system apps are running."
        
        apps_list = "\n".join([f"• {app}" for app in user_apps[:15]])
        return f"📱 Running Apps:\n{apps_list}"
    except Exception as e:
        return f"❌ Failed to list apps: {str(e)}"


def switch_to_app(app_name):
    """Bring an application to the foreground"""
    try:
        actual_name = _get_app_name(app_name)
        subprocess.run([
            "osascript", "-e",
            f'tell application "{actual_name}" to activate'
        ], check=True)
        return f"✅ Switched to {actual_name}"
    except Exception as e:
        return f"❌ Failed to switch to {app_name}: {str(e)}"


def kill_app(app_name):
    """Force quit an application"""
    try:
        actual_name = _get_app_name(app_name)
        subprocess.run(["pkill", "-9", "-f", actual_name], check=False)
        return f"💀 Force quit {actual_name}"
    except Exception as e:
        return f"❌ Failed to kill {app_name}: {str(e)}"


def get_frontmost_app():
    """Get the currently active application"""
    try:
        result = subprocess.run([
            "osascript", "-e",
            'tell application "System Events" to get name of first process whose frontmost is true'
        ], capture_output=True, text=True)
        app = result.stdout.strip()
        return f"🎯 Current app: {app}"
    except Exception as e:
        return f"❌ Failed to get current app: {str(e)}"
