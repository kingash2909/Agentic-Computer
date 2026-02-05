"""
Media Controller - Handles media playback (Spotify, Apple Music)
Supports: play, pause, next, previous, current info
"""

import subprocess
import platform

try:
    import pyautogui
except ImportError:
    pyautogui = None

def play_pause():
    """Toggle play/pause on active media player"""
    try:
        if platform.system() == "Darwin":
            # keyCode 100 is Play/Pause on macOS
            subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 100'], check=True)
        else:
            if pyautogui:
                pyautogui.press('playpause')
        return "⏯️ Toggled Play/Pause"
    except Exception as e:
        return f"❌ Failed: {str(e)}"

def next_track():
    """Skip to next track"""
    try:
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 101'], check=True)
        else:
            if pyautogui:
                pyautogui.press('nexttrack')
        return "⏭️ Skipped to next track"
    except Exception as e:
        return f"❌ Failed: {str(e)}"

def prev_track():
    """Go to previous track"""
    try:
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 98'], check=True)
        else:
            if pyautogui:
                pyautogui.press('prevtrack')
        return "⏮️ Previous track"
    except Exception as e:
        return f"❌ Failed: {str(e)}"

def get_now_playing():
    """Get information about currently playing track (Best effort)"""
    if platform.system() == "Darwin":
        # Check Spotify
        try:
            script = 'tell application "Spotify" to if player state is playing then return "Spotify: " & name of current track & " by " & artist of current track'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.stdout.strip(): return f"🎵 {result.stdout.strip()}"
        except: pass

        # Check Music
        try:
            script = 'tell application "Music" to if player state is playing then return "Music: " & name of current track & " by " & artist of current track'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.stdout.strip(): return f"🎵 {result.stdout.strip()}"
        except: pass

    return "🔇 Media playback detected (Generic)." if platform.system() != "Darwin" else "🔇 Nothing playing right now"
