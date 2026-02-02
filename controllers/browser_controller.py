"""
Browser Controller - Handles browser automation
Supports: open URL, search Google, close browser
"""

import subprocess
import urllib.parse


def open_url(url):
    """Open a URL in the default browser"""
    try:
        # Add https if no protocol specified
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        subprocess.run(["open", url], check=True)
        return f"🌐 Opened {url}"
    except Exception as e:
        return f"❌ Failed to open URL: {str(e)}"


def search_google(query):
    """Perform a Google search"""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        subprocess.run(["open", url], check=True)
        return f"🔍 Searching Google for: {query}"
    except Exception as e:
        return f"❌ Failed to search: {str(e)}"


def search_youtube(query):
    """Search on YouTube"""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        subprocess.run(["open", url], check=True)
        return f"▶️ Searching YouTube for: {query}"
    except Exception as e:
        return f"❌ Failed to search YouTube: {str(e)}"


def open_youtube():
    """Open YouTube"""
    return open_url("https://www.youtube.com")


def open_gmail():
    """Open Gmail"""
    return open_url("https://mail.google.com")


def open_google_meet():
    """Open Google Meet"""
    return open_url("https://meet.google.com")


def open_github():
    """Open GitHub"""
    return open_url("https://github.com")


def close_browser():
    """Close Chrome browser"""
    try:
        subprocess.run([
            "osascript", "-e",
            'tell application "Google Chrome" to quit'
        ], check=True)
        return "✅ Closed Chrome"
    except Exception as e:
        return f"❌ Failed to close browser: {str(e)}"


def new_tab(url=None):
    """Open a new tab in Chrome"""
    try:
        if url:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            script = f'''
            tell application "Google Chrome"
                activate
                make new tab at end of tabs of window 1
                set URL of active tab of window 1 to "{url}"
            end tell
            '''
        else:
            script = '''
            tell application "Google Chrome"
                activate
                make new tab at end of tabs of window 1
            end tell
            '''
        subprocess.run(["osascript", "-e", script], check=True)
        return f"✅ Opened new tab" + (f" with {url}" if url else "")
    except Exception as e:
        return f"❌ Failed to open new tab: {str(e)}"


def close_tab():
    """Close current tab in Chrome"""
    try:
        script = '''
        tell application "Google Chrome"
            close active tab of window 1
        end tell
        '''
        subprocess.run(["osascript", "-e", script], check=True)
        return "✅ Closed current tab"
    except Exception as e:
        return f"❌ Failed to close tab: {str(e)}"
