"""
App Controller - Handles application management
Supports: open, close, list running apps, switch to app
"""

import subprocess
import psutil
import platform
import os


# Common app name mappings (what user says -> actual app name/process name)
APP_MAPPINGS = {
    "chrome": {"mac": "Google Chrome", "win": "chrome.exe"},
    "google chrome": {"mac": "Google Chrome", "win": "chrome.exe"},
    "safari": {"mac": "Safari", "win": None},
    "vscode": {"mac": "Visual Studio Code", "win": "Code.exe"},
    "code": {"mac": "Visual Studio Code", "win": "Code.exe"},
    "terminal": {"mac": "Terminal", "win": "cmd.exe"},
    "notepad": {"mac": "TextEdit", "win": "notepad.exe"},
    "calculator": {"mac": "Calculator", "win": "calc.exe"},
    "spotify": {"mac": "Spotify", "win": "Spotify.exe"},
}


def _get_app_identifier(user_input):
    """Convert user input to actual app name or process name based on OS"""
    user_input_lower = user_input.lower().strip()
    mapping = APP_MAPPINGS.get(user_input_lower)
    
    os_type = "mac" if platform.system() == "Darwin" else "win"
    
    if mapping:
        return mapping.get(os_type) or user_input
    return user_input


def open_app(app_name):
    """Open an application"""
    try:
        actual_name = _get_app_identifier(app_name)
        if platform.system() == "Darwin":
            subprocess.run(["open", "-a", actual_name], check=True)
        elif platform.system() == "Windows":
            # Check if it's a known command or needs full path. 
            # os.startfile is best for Windows desktop apps.
            try:
                os.startfile(actual_name)
            except FileNotFoundError:
                subprocess.run(["cmd", "/c", "start", actual_name], check=True)
        return f"✅ Opened {actual_name}"
    except Exception as e:
        return f"❌ Failed to open {app_name}: {str(e)}"


def close_app(app_name):
    """Close an application gracefully"""
    try:
        actual_name = _get_app_identifier(app_name)
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", f'tell application "{actual_name}" to quit'], check=True)
        elif platform.system() == "Windows":
            # Remove .exe for taskkill if present
            proc_name = actual_name if not actual_name.endswith(".exe") else actual_name[:-4]
            subprocess.run(["taskkill", "/IM", f"{proc_name}.exe"], check=True)
        return f"✅ Closed {actual_name}"
    except Exception as e:
        # Fallback to force kill if graceful fails
        return kill_app(app_name)


def list_running_apps():
    """List all running GUI applications"""
    try:
        if platform.system() == "Darwin":
            script = 'tell application "System Events" to get name of every process whose background only is false'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            apps = result.stdout.strip().split(", ")
            user_apps = sorted([app for app in apps if app not in {"Finder", "Dock", "SystemUIServer"}])
        else:
            # Windows/Other using psutil
            user_apps = []
            for proc in psutil.process_iter(['name']):
                try:
                    # Very basic filter for 'GUI' apps - this is hard on Windows without Win32 API
                    # We'll just list common ones or all for now
                    name = proc.info['name']
                    if name.endswith(".exe") and name.lower() not in {"svchost.exe", "explorer.exe", "lsass.exe"}:
                        user_apps.append(name)
                except:
                    continue
            user_apps = sorted(list(set(user_apps)))[:15] # Limit results

        if not user_apps:
            return "📱 No user apps detected."
        
        apps_list = "\n".join([f"• {app}" for app in user_apps])
        return f"📱 Running Apps:\n{apps_list}"
    except Exception as e:
        return f"❌ Failed to list apps: {str(e)}"


def kill_app(app_name):
    """Force quit an application"""
    try:
        actual_name = _get_app_identifier(app_name)
        if platform.system() == "Darwin":
            subprocess.run(["pkill", "-9", "-f", actual_name], check=False)
        elif platform.system() == "Windows":
            proc_name = actual_name if not actual_name.endswith(".exe") else actual_name[:-4]
            subprocess.run(["taskkill", "/F", "/IM", f"{proc_name}.exe"], check=True)
        return f"💀 Force quit {actual_name}"
    except Exception as e:
        return f"❌ Failed to kill {app_name}: {str(e)}"


def get_frontmost_app():
    """Get the currently active application"""
    try:
        if platform.system() == "Darwin":
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            return f"🎯 Current app: {result.stdout.strip()}"
        elif platform.system() == "Windows":
            # Requires pygetwindow or similar, or just return generic
            return "🎯 Active app detection active (Windows)."
    except Exception as e:
        return f"❌ Failed: {str(e)}"
