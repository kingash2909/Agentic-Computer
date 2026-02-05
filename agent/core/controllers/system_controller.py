"""
System Controller - Handles system-level operations
Supports: shutdown, restart, sleep, lock, volume, brightness, battery
"""

import subprocess
import psutil
import datetime
import time
import platform
import os

try:
    import screen_brightness_control as sbc
except ImportError:
    sbc = None

try:
    import pyperclip
except ImportError:
    pyperclip = None

def shutdown():
    """Shutdown the computer"""
    try:
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", 'tell app "System Events" to shut down'], check=True)
        elif platform.system() == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "1"], check=True)
        return "🔌 Shutting down your computer..."
    except Exception as e:
        return f"❌ Failed to shutdown: {str(e)}"


def restart():
    """Restart the computer"""
    try:
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", 'tell app "System Events" to restart'], check=True)
        elif platform.system() == "Windows":
            subprocess.run(["shutdown", "/r", "/t", "1"], check=True)
        return "🔄 Restarting your computer..."
    except Exception as e:
        return f"❌ Failed to restart: {str(e)}"


def sleep():
    """Put computer to sleep"""
    try:
        if platform.system() == "Darwin":
            subprocess.run(["pmset", "sleepnow"], check=True)
        elif platform.system() == "Windows":
            # Requires powercfg or specific rundll32 call
            subprocess.run(["rundll32.exe", "powprof.dll,SetSuspendState", "0,1,0"], check=True)
        return "😴 Putting computer to sleep..."
    except Exception as e:
        return f"❌ Failed to sleep: {str(e)}"


def lock_screen():
    """Lock the screen"""
    try:
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "q" using {command down, control down}'], check=True)
        elif platform.system() == "Windows":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
        return "🔒 Screen locked!"
    except Exception as e:
        return f"❌ Failed to lock: {str(e)}"


def set_volume(level):
    """Set system volume (0-100)"""
    try:
        level = max(0, min(100, int(level)))
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
        elif platform.system() == "Windows":
            # On Windows, we need an external tool or library like comtypes/pycaw
            # For now, we'll try to use a simple nircmd if available, or just use pyautogui as fallback
            import pyautogui
            for _ in range(50): pyautogui.press('volumedown')
            for _ in range(level // 2): pyautogui.press('volumeup')
        return f"🔊 Volume set to {level}%"
    except Exception as e:
        return f"❌ Failed to set volume: {str(e)}"


def get_volume():
    """Get current volume level"""
    try:
        if platform.system() == "Darwin":
            result = subprocess.run(["osascript", "-e", "output volume of (get volume settings)"], capture_output=True, text=True)
            volume = result.stdout.strip()
            return f"🔊 Current volume: {volume}%"
        elif platform.system() == "Windows":
            # Difficult without heavy libraries, returning placeholder
            return "🔊 Volume control active (Windows)."
    except Exception as e:
        return f"❌ Failed to get volume: {str(e)}"


def mute():
    """Mute system volume"""
    try:
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", "set volume output muted true"], check=True)
        elif platform.system() == "Windows":
            import pyautogui
            pyautogui.press('volumemute')
        return "🔇 Volume muted!"
    except Exception as e:
        return f"❌ Failed to mute: {str(e)}"


def unmute():
    """Unmute system volume"""
    try:
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", "set volume output muted false"], check=True)
        elif platform.system() == "Windows":
            import pyautogui
            pyautogui.press('volumemute') # Toggles mute on Windows
        return "🔊 Volume unmuted!"
    except Exception as e:
        return f"❌ Failed to unmute: {str(e)}"


def set_brightness(level):
    """Set screen brightness (0-100)"""
    try:
        level = max(0, min(100, int(level)))
        if sbc:
            sbc.set_brightness(level)
            return f"☀️ Brightness set to {level}%"
        return "⚠️ Brightness control requires 'screen-brightness-control' library."
    except Exception as e:
        return f"❌ Failed to set brightness: {str(e)}"


def get_battery():
    """Get battery status"""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "🔌 No battery detected."
        
        percent = battery.percent
        plugged = battery.power_plugged
        time_left = battery.secsleft
        
        status = "🔌 Charging" if plugged else "🔋 On Battery"
        time_str = ""
        if time_left > 0 and not plugged:
            hours = time_left // 3600
            minutes = (time_left % 3600) // 60
            time_str = f" ({hours}h {minutes}m remaining)"
        
        return f"{status}: {percent:.0f}%{time_str}"
    except Exception as e:
        return f"❌ Failed to get battery: {str(e)}"


def get_system_info():
    """Get basic system information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        
        # Cross-platform disk info
        root_path = "C:\\" if platform.system() == "Windows" else "/"
        disk = psutil.disk_usage(root_path)
        
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        uptime = time.time() - psutil.boot_time()
        uptime_str = str(datetime.timedelta(seconds=int(uptime)))
        
        os_info = f"{platform.system()} {platform.release()}"
        
        return f"""📊 System Status ({os_info}):
• CPU: {cpu_percent}% used
• RAM: {memory.percent}% used ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)
• Disk: {disk.percent}% used ({disk.free // (1024**3)}GB free)
• Boot Time: {boot_time}
• Uptime: {uptime_str}"""
    except Exception as e:
        return f"❌ Failed to get system info: {str(e)}"

def get_clipboard():
    """Get clipboard content"""
    try:
        if pyperclip:
            return pyperclip.paste()
        # Fallback for Mac
        if platform.system() == "Darwin":
            return subprocess.check_output("pbpaste", env={'LANG': 'en_US.UTF-8'}).decode('utf-8')
        return "❌ pyperclip not installed."
    except Exception as e:
        return f"❌ Failed to get clipboard: {str(e)}"

def set_clipboard(text):
    """Set clipboard content"""
    try:
        if pyperclip:
            pyperclip.copy(text)
            return "📋 Clipboard updated!"
        # Fallback for Mac
        if platform.system() == "Darwin":
            process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            return "📋 Clipboard updated!"
        return "❌ pyperclip not installed."
    except Exception as e:
        return f"❌ Failed to set clipboard: {str(e)}"

