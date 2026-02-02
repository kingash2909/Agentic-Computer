"""
System Controller - Handles system-level operations
Supports: shutdown, restart, sleep, lock, volume, brightness, battery
"""

import subprocess
import psutil


def shutdown():
    """Shutdown the computer"""
    try:
        subprocess.run(["osascript", "-e", 'tell app "System Events" to shut down'], check=True)
        return "🔌 Shutting down your computer..."
    except Exception as e:
        return f"❌ Failed to shutdown: {str(e)}"


def restart():
    """Restart the computer"""
    try:
        subprocess.run(["osascript", "-e", 'tell app "System Events" to restart'], check=True)
        return "🔄 Restarting your computer..."
    except Exception as e:
        return f"❌ Failed to restart: {str(e)}"


def sleep():
    """Put computer to sleep"""
    try:
        subprocess.run(["pmset", "sleepnow"], check=True)
        return "😴 Putting your Mac to sleep..."
    except Exception as e:
        return f"❌ Failed to sleep: {str(e)}"


def lock_screen():
    """Lock the screen"""
    try:
        subprocess.run([
            "osascript", "-e",
            'tell application "System Events" to keystroke "q" using {command down, control down}'
        ], check=True)
        return "🔒 Screen locked!"
    except Exception as e:
        return f"❌ Failed to lock: {str(e)}"


def set_volume(level):
    """Set system volume (0-100)"""
    try:
        # macOS volume is 0-100
        level = max(0, min(100, int(level)))
        # Convert to macOS scale (0-7 for osascript output volume)
        mac_level = int(level * 7 / 100)
        subprocess.run([
            "osascript", "-e", f"set volume output volume {level}"
        ], check=True)
        return f"🔊 Volume set to {level}%"
    except Exception as e:
        return f"❌ Failed to set volume: {str(e)}"


def get_volume():
    """Get current volume level"""
    try:
        result = subprocess.run([
            "osascript", "-e", "output volume of (get volume settings)"
        ], capture_output=True, text=True)
        volume = result.stdout.strip()
        return f"🔊 Current volume: {volume}%"
    except Exception as e:
        return f"❌ Failed to get volume: {str(e)}"


def mute():
    """Mute system volume"""
    try:
        subprocess.run(["osascript", "-e", "set volume output muted true"], check=True)
        return "🔇 Volume muted!"
    except Exception as e:
        return f"❌ Failed to mute: {str(e)}"


def unmute():
    """Unmute system volume"""
    try:
        subprocess.run(["osascript", "-e", "set volume output muted false"], check=True)
        return "🔊 Volume unmuted!"
    except Exception as e:
        return f"❌ Failed to unmute: {str(e)}"


def set_brightness(level):
    """Set screen brightness (0-100)"""
    try:
        level = max(0, min(100, int(level)))
        # Convert to 0-1 scale for brightness
        brightness = level / 100
        subprocess.run([
            "osascript", "-e",
            f'tell application "System Preferences" to set brightness of display 1 to {brightness}'
        ], check=True)
        return f"☀️ Brightness set to {level}%"
    except Exception as e:
        # Fallback message - brightness control may need additional permissions
        return f"⚠️ Brightness control may need System Preferences permissions. Try manually."


def get_battery():
    """Get battery status"""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "🔌 No battery detected (desktop Mac?)"
        
        percent = battery.percent
        plugged = battery.power_plugged
        time_left = battery.secsleft
        
        status = "🔌 Charging" if plugged else "🔋 On Battery"
        
        if time_left > 0 and not plugged:
            hours = time_left // 3600
            minutes = (time_left % 3600) // 60
            time_str = f" ({hours}h {minutes}m remaining)"
        else:
            time_str = ""
        
        return f"{status}: {percent:.0f}%{time_str}"
    except Exception as e:
        return f"❌ Failed to get battery: {str(e)}"


def get_system_info():
    """Get basic system information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return f"""📊 System Status:
• CPU: {cpu_percent}% used
• RAM: {memory.percent}% used ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)
• Disk: {disk.percent}% used ({disk.free // (1024**3)}GB free)"""
    except Exception as e:
        return f"❌ Failed to get system info: {str(e)}"
