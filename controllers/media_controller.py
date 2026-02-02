"""
Media Controller - Handles media playback (Spotify, Apple Music)
Supports: play, pause, next, previous, current info
"""

import subprocess

def _run_spotify_command(command):
    """Run AppleScript command for Spotify"""
    try:
        script = f'tell application "Spotify" to {command}'
        subprocess.run(["osascript", "-e", script], check=True)
        return True
    except:
        return False

def _run_music_command(command):
    """Run AppleScript command for Apple Music"""
    try:
        script = f'tell application "Music" to {command}'
        subprocess.run(["osascript", "-e", script], check=True)
        return True
    except:
        return False

def play_pause():
    """Toggle play/pause on active media player via media keys"""
    try:
        # Simulate media key press which works for any active player
        # keyCode 100 is Play/Pause on macOS
        script = 'tell application "System Events" to key code 100'
        subprocess.run(["osascript", "-e", script], check=True)
        return "⏯️ Toggled Play/Pause"
    except Exception as e:
        return f"❌ Failed to toggle media: {str(e)}"

def next_track():
    """Skip to next track"""
    try:
        script = 'tell application "System Events" to key code 101'
        subprocess.run(["osascript", "-e", script], check=True)
        return "⏭️ Skipped to next track"
    except Exception as e:
        return f"❌ Failed to skip track: {str(e)}"

def prev_track():
    """Go to previous track"""
    try:
        script = 'tell application "System Events" to key code 98'
        subprocess.run(["osascript", "-e", script], check=True)
        return "⏮️ Previous track"
    except Exception as e:
        return f"❌ Failed to go back: {str(e)}"

def get_now_playing():
    """Get information about currently playing track"""
    # Try Spotify first
    try:
        script = '''
        tell application "Spotify"
            if player state is playing then
                set trackName to name of current track
                set artistName to artist of current track
                return "Spotify: " & trackName & " by " & artistName
            end if
        end tell
        '''
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.stdout.strip():
            return f"🎵 {result.stdout.strip()}"
    except:
        pass

    # Try Apple Music
    try:
        script = '''
        tell application "Music"
            if player state is playing then
                set trackName to name of current track
                set artistName to artist of current track
                return "Music: " & trackName & " by " & artistName
            end if
        end tell
        '''
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.stdout.strip():
            return f"🎵 {result.stdout.strip()}"
    except:
        pass

    return "🔇 Nothing playing right now"
