
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers import system_controller, app_controller, file_controller, browser_controller, media_controller

def test_system_commands():
    print("\n🖥️ Testing System Commands...")
    try:
        print(f"   Battery: {system_controller.get_battery()}")
    except Exception as e: print(f"   ❌ Battery Failed: {e}")
    
    try:
        print(f"   Info: {system_controller.get_system_info()}")
    except Exception as e: print(f"   ❌ Info Failed: {e}")
    
    try:
        # Toggle mute to test volume control without blasting sound
        print("   Testing Mute/Unmute...")
        system_controller.mute()
        time.sleep(0.5)
        system_controller.unmute()
        print("   ✅ Mute/Unmute executed")
    except Exception as e: print(f"   ❌ Audio Control Failed: {e}")

def test_app_commands():
    print("\n📱 Testing App Commands...")
    try:
        apps = app_controller.list_running_apps()
        print(f"   Runnings Apps: Found {len(apps.split(','))} apps")
    except Exception as e: print(f"   ❌ List Apps Failed: {e}")
    
    try:
        front = app_controller.get_frontmost_app()
        print(f"   Frontmost App: {front}")
    except Exception as e: print(f"   ❌ Current App Failed: {e}")

def test_file_commands():
    print("\n📂 Testing File Commands...")
    try:
        space = file_controller.get_disk_space()
        print(f"   Disk Space: {space}")
    except Exception as e: print(f"   ❌ Disk Space Failed: {e}")
    
    try:
        # Search for this script
        results = file_controller.find_file("check_commands.py")
        print(f"   Find File: {results}")
    except Exception as e: print(f"   ❌ Find File Failed: {e}")

def test_browser_commands():
    print("\n🌐 Testing Browser Commands...")
    # Skipping actual browser opening to avoid spamming windows
    print("   (Skipping interactive browser tests)")

def test_media_commands():
    print("\n🎵 Testing Media Commands...")
    try:
        now = media_controller.get_now_playing()
        print(f"   Now Playing: {now}")
    except Exception as e: print(f"   ❌ Now Playing Failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Command Check...")
    test_system_commands()
    test_app_commands()
    test_file_commands()
    test_browser_commands()
    test_media_commands()
    print("\n✅ Check Complete. If actual commands fail via WhatsApp but pass here, the issue is likely in 'Intent Parsing'.")
