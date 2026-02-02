"""
File Controller - Handles file system operations
Supports: find files, list directory, disk space, screenshots
"""

import subprocess
import os
from datetime import datetime
import psutil

# Screenshots directory
SCREENSHOTS_DIR = os.path.expanduser("~/Desktop/AgenticScreenshots")


def find_file(filename):
    """Search for a file on the system"""
    try:
        # Search in common directories
        search_paths = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~"),
        ]
        
        found_files = []
        for search_path in search_paths:
            result = subprocess.run(
                ["find", search_path, "-maxdepth", "3", "-iname", f"*{filename}*", "-type", "f"],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout:
                found_files.extend(result.stdout.strip().split("\n")[:5])
        
        if not found_files:
            return f"🔍 No files found matching '{filename}'"
        
        # Limit results
        found_files = found_files[:10]
        files_list = "\n".join([f"• {os.path.basename(f)}\n  📁 {os.path.dirname(f)}" for f in found_files])
        return f"🔍 Found {len(found_files)} file(s):\n{files_list}"
    except subprocess.TimeoutExpired:
        return "⏱️ Search took too long. Try a more specific filename."
    except Exception as e:
        return f"❌ Search failed: {str(e)}"


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
        
        # Separate files and folders
        folders = []
        files = []
        for item in items:
            if item.startswith('.'):
                continue  # Skip hidden files
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                folders.append(f"📁 {item}/")
            else:
                size = os.path.getsize(full_path)
                size_str = _format_size(size)
                files.append(f"📄 {item} ({size_str})")
        
        result = f"📂 Contents of {os.path.basename(path)}:\n"
        if folders:
            result += "\n".join(folders[:10]) + "\n"
        if files:
            result += "\n".join(files[:10])
        
        total = len(folders) + len(files)
        if total > 20:
            result += f"\n... and {total - 20} more items"
        
        return result
    except Exception as e:
        return f"❌ Failed to list directory: {str(e)}"


def _format_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def get_disk_space():
    """Get disk space information"""
    try:
        disk = psutil.disk_usage('/')
        total = disk.total / (1024**3)
        used = disk.used / (1024**3)
        free = disk.free / (1024**3)
        percent = disk.percent
        
        return f"""💾 Disk Space:
• Total: {total:.1f} GB
• Used: {used:.1f} GB ({percent}%)
• Free: {free:.1f} GB"""
    except Exception as e:
        return f"❌ Failed to get disk space: {str(e)}"


def take_screenshot():
    """Take a screenshot and save it"""
    try:
        # Create screenshots directory if it doesn't exist
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        
        # Take screenshot using macOS screencapture
        subprocess.run(["screencapture", "-x", filepath], check=True)
        
        if os.path.exists(filepath):
            return filepath  # Return path for sending via WhatsApp
        else:
            return None
    except Exception as e:
        return None


def get_downloads():
    """List recent downloads"""
    try:
        downloads_path = os.path.expanduser("~/Downloads")
        files = []
        
        for item in os.listdir(downloads_path):
            if item.startswith('.'):
                continue
            full_path = os.path.join(downloads_path, item)
            if os.path.isfile(full_path):
                mtime = os.path.getmtime(full_path)
                size = os.path.getsize(full_path)
                files.append((item, mtime, size))
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x[1], reverse=True)
        files = files[:10]
        
        if not files:
            return "📥 No files in Downloads folder"
        
        result = "📥 Recent Downloads:\n"
        for name, mtime, size in files:
            date = datetime.fromtimestamp(mtime).strftime("%b %d")
            result += f"• {name} ({_format_size(size)}) - {date}\n"
        
        return result.strip()
    except Exception as e:
        return f"❌ Failed to get downloads: {str(e)}"
