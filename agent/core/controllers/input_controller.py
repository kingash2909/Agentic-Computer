"""
Input Controller - Simulates mouse and keyboard input using pyautogui
"""

import pyautogui
import time

# Disable fail-safe if the user really wants full control, 
# but it's safer to keep it enabled (move mouse to corner to stop).
pyautogui.FAILSAFE = True

def click(x=None, y=None, clicks=1, button='left'):
    """Click at specific coordinates or current position"""
    try:
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y, clicks=clicks, button=button)
            return f"✅ Clicked {button} at ({x}, {y})"
        else:
            pyautogui.click(clicks=clicks, button=button)
            return f"✅ Clicked {button} at current position"
    except Exception as e:
        return f"❌ Click failed: {str(e)}"

def type_text(text, interval=0.1):
    """Type string of text"""
    try:
        pyautogui.write(text, interval=interval)
        return f"✅ Typed: {text}"
    except Exception as e:
        return f"❌ Typing failed: {str(e)}"

def press_key(key):
    """Press a specific key (e.g. 'enter', 'tab', 'esc')"""
    try:
        pyautogui.press(key)
        return f"✅ Pressed key: {key}"
    except Exception as e:
        return f"❌ Key press failed: {str(e)}"

def hotkey(*args):
    """Perform hotkey combination (e.g. 'command', 'c')"""
    try:
        pyautogui.hotkey(*args)
        return f"✅ Performed hotkey: {'+'.join(args)}"
    except Exception as e:
        return f"❌ Hotkey failed: {str(e)}"

def move_to(x, y):
    """Move mouse to coordinates"""
    try:
        pyautogui.moveTo(x, y, duration=0.5)
        return f"✅ Moved mouse to ({x}, {y})"
    except Exception as e:
        return f"❌ Movement failed: {str(e)}"

def get_screen_info():
    """Get screen resolution and mouse position"""
    try:
        width, height = pyautogui.size()
        x, y = pyautogui.position()
        return f"🖥️ Screen: {width}x{height}\n🖱️ Mouse at: ({x}, {y})"
    except Exception as e:
        return f"❌ Info failed: {str(e)}"
