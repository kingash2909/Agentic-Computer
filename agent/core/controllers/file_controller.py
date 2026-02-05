"""
File Controller - Handles file system operations
Supports: find files, list directory, disk space, screenshots
"""

import subprocess
import os
from datetime import datetime
import psutil
import platform

try:
    import pyautogui
except ImportError:
    pyautogui = None

# Screenshots directory
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "screenshots")

def find_file(filename):
    """Search for a file (Spotlight on Mac, dir on Windows)"""
    try:
        if platform.system() == "Darwin":
            # Use mdfind (Spotlight) for instant search
            result = subprocess.run(["mdfind", "-name", filename], capture_output=True, text=True, timeout=5)
            if not result.stdout.strip():
                return _find_file_fallback(filename)
            found_files = result.stdout.strip().split('\n')
        elif platform.system() == "Windows":
            # Use dir command on Windows (can be slow on large drives)
            # Focus on common user folders for speed
            search_paths = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents"), os.path.expanduser("~/Downloads")]
            found_files = []
            for path in search_paths:
                try:
                    res = subprocess.run(["cmd", "/c", f"dir /s /b {filename}"], cwd=path, capture_output=True, text=True, timeout=5)
                    if res.stdout.strip():
                        found_files.extend(res.stdout.strip().split('\n'))
                except:
                    continue
        else:
            return _find_file_fallback(filename)

        # Filter and format results
        clean_files = [f for f in found_files if '/Library/' not in f and '/System/' not in f and '/.' not in f]
        if not clean_files:
             return f"🔍 No relevant files found matching '{filename}'"

        clean_files = clean_files[:10]
        files_list = "\n".join([f"• {os.path.basename(f)}\n  📁 {os.path.dirname(f)}" for f in clean_files])
        return f"🔍 Found {len(clean_files)} file(s):\n{files_list}"

    except Exception as e:
        return f"❌ Search failed: {str(e)}"

def _find_file_fallback(filename):
    """Fallback search using find command (Unix only)"""
    try:
        if platform.system() == "Windows":
             return "🔍 No files found."
             
        search_paths = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents"), os.path.expanduser("~/Downloads")]
        found_files = []
        for search_path in search_paths:
            result = subprocess.run(["find", search_path, "-maxdepth", "2", "-iname", f"*{filename}*"], capture_output=True, text=True, timeout=5)
            if result.stdout:
                found_files.extend(result.stdout.strip().split("\n")[:5])
        
        if not found_files:
            return f"🔍 No files found matching '{filename}'"
            
        files_list = "\n".join([f"• {os.path.basename(f)}" for f in found_files])
        return f"🔍 Found (Slow Search):\n{files_list}"
    except Exception:
        return "🔍 No files found."


def list_directory(path=None):
    """List contents of a directory"""
    try:
        if path is None:
            path = os.path.expanduser("~/Desktop")
        else:
            path = os.path.expanduser(path)
        
        if not os.path.exists(path):
            return f"❌ Directory not found: {path}"
        
        items = os.listdir(path)
        folders, files = [], []
        for item in items:
            if item.startswith('.'): continue
            full_path = os.path.join(path, item)
            try:
                if os.path.isdir(full_path):
                    folders.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(full_path)
                    files.append(f"📄 {item} ({_format_size(size)})")
            except: continue
        
        result = f"📂 Contents of {os.path.basename(path)}:\n"
        result += "\n".join(folders[:10]) + "\n" + "\n".join(files[:10])
        return result
    except Exception as e:
        return f"❌ Failed: {str(e)}"


def _format_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024: return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def get_disk_space():
    """Get disk space information"""
    try:
        root = "C:\\" if platform.system() == "Windows" else "/"
        disk = psutil.disk_usage(root)
        total = disk.total / (1024**3)
        free = disk.free / (1024**3)
        return f"💾 Disk ({root}): {disk.percent}% used ({free:.1f} GB free of {total:.1f} GB)"
    except Exception as e:
        return f"❌ Failed: {str(e)}"


def take_screenshot():
    """Take a screenshot using pyautogui (cross-platform)"""
    try:
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        
        if pyautogui:
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            return filepath
        elif platform.system() == "Darwin":
            # Fallback to Mac screencapture if no pyautogui
            subprocess.run(["screencapture", "-x", filepath], check=True)
            return filepath
        return None
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None


def get_downloads():
    """List recent downloads"""
    try:
        downloads_path = os.path.expanduser("~/Downloads")
        files = []
        if not os.path.exists(downloads_path): return "❌ Downloads folder not found."
             
        for item in os.listdir(downloads_path):
            if item.startswith('.'): continue
            full_path = os.path.join(downloads_path, item)
            try:
                if os.path.isfile(full_path):
                    files.append((item, os.path.getmtime(full_path), os.path.getsize(full_path)))
            except: continue
        
        files.sort(key=lambda x: x[1], reverse=True)
        files = files[:10]
        if not files: return "📥 No files in Downloads"
        
        result = "📥 Recent Downloads:\n"
        for name, mtime, size in files:
            result += f"• {name} ({_format_size(size)})\n"
        return result.strip()
    except Exception as e:
        return f"❌ Failed: {str(e)}"

def get_file(path):
    """Read a file and return its path for sending"""
    try:
        path = os.path.expanduser(path)
        if os.path.exists(path) and os.path.isfile(path):
            if os.path.getsize(path) > 10 * 1024 * 1024:
                return "❌ File too large (>10MB)."
            return path
        return "❌ File not found."
    except Exception as e:
        return f"❌ Error: {str(e)}"
