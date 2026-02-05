import eventlet
eventlet.monkey_patch()

import sys
import os
import socketio
import base64
import threading
import time

# Add root dir to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from agent.core.controllers import system_controller, app_controller, file_controller, browser_controller, media_controller, shell_controller, input_controller

class AgentClient:
    def __init__(self, server_url, on_log=None, on_status_change=None):
        self.server_url = server_url
        self.sio = socketio.Client()
        self.on_log = on_log if on_log else print
        self.on_status_change = on_status_change
        self.pairing_code = None
        
        # Register events
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('connect_error', self._on_connect_error)
        self.sio.on('registration_success', self._on_registration_success)
        self.sio.on('registration_failed', self._on_registration_failed)
        self.sio.on('execute_command', self._on_execute_command)

    def connect(self, code):
        """Connect to server with pairing code"""
        self.pairing_code = code
        self.log(f"🔄 Connecting to {self.server_url}...")
        try:
            self.sio.connect(self.server_url)
            # Register is handled in _on_connect or explicitly here if needed. 
            # But usually we wait for connect event.
            # However, socketio client connect is blocking until connected or error,
            # so we can emit right after.
            self.sio.emit('register', {'code': code})
            
            # Start a background thread to wait if running in CLI mode, 
            # but for GUI we don't want to block.
            # self.sio.wait() 
        except Exception as e:
            self.log(f"❌ Connection error: {e}")
            if self.on_status_change: self.on_status_change("disconnected")

    def disconnect(self):
        if self.sio.connected:
            self.sio.disconnect()

    def log(self, message):
        self.on_log(message)

    def _on_connect(self):
        self.log("✅ Connected to Server socket")
        if self.on_status_change: self.on_status_change("connected")

    def _on_disconnect(self):
        self.log("❌ Disconnected from Server")
        if self.on_status_change: self.on_status_change("disconnected")
        
    def _on_connect_error(self, data):
        self.log(f"❌ Connection failed: {data}")
        if self.on_status_change: self.on_status_change("disconnected")

    def _on_registration_success(self, data):
        self.log("🎉 Successfully paired with WhatsApp!")
        if self.on_status_change: self.on_status_change("paired")

    def _on_registration_failed(self, data):
        self.log(f"❌ Pairing failed: {data.get('reason')}")
        self.disconnect()

    def _on_execute_command(self, intent):
        """Receive command from server and execute it"""
        self.log(f"📥 Received Command: {intent.get('action')} -> {intent.get('command')}")
        
        action = intent.get("action")
        command = intent.get("command")
        params = intent.get("params", {})
        
        result = None
        
        try:
            # --- SYSTEM COMMANDS ---
            if action == "system":
                if command == "shutdown": result = system_controller.shutdown()
                elif command == "restart": result = system_controller.restart()
                elif command == "sleep": result = system_controller.sleep()
                elif command == "lock": result = system_controller.lock_screen()
                elif command == "volume": result = system_controller.set_volume(params.get("level", 50))
                elif command == "mute": result = system_controller.mute()
                elif command == "unmute": result = system_controller.unmute()
                elif command == "battery": result = system_controller.get_battery()
                elif command == "info": result = system_controller.get_system_info()
                elif command == "brightness": result = system_controller.set_brightness(params.get("level", 50))
                elif command == "clipboard": result = system_controller.get_clipboard()
                elif command == "screenshot": 
                    path = file_controller.take_screenshot()
                    if path and not path.startswith("❌"): 
                        try:
                            with open(path, "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                            result = "Screenshot captured"
                            self.sio.emit('command_result', {'output': result, 'image_data': encoded_string})
                            return 
                        except Exception as e:
                            result = f"Failed to process screenshot: {e}"
                    else: result = f"Failed to take screenshot: {path if path else 'Unknown error'}"
                elif command == "connect": return 
            
            # --- APP COMMANDS ---
            elif action == "app":
                if command == "open": result = app_controller.open_app(params.get("app_name", ""))
                elif command == "close": result = app_controller.close_app(params.get("app_name", ""))
                elif command in ["list", "list_apps", "running_apps"]: result = app_controller.list_running_apps()
                elif command == "switch": result = app_controller.switch_to_app(params.get("app_name", ""))
                elif command == "kill": result = app_controller.kill_app(params.get("app_name", ""))
                elif command in ["current", "current_app"]: result = app_controller.get_frontmost_app()
            
            # --- FILE COMMANDS ---
            elif action == "file":
                if command == "screenshot": 
                    path = file_controller.take_screenshot()
                    if path and not path.startswith("❌"): 
                        try:
                            with open(path, "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                            result = "Screenshot captured"
                            self.sio.emit('command_result', {'output': result, 'image_data': encoded_string})
                            return 
                        except Exception as e:
                            result = f"Failed to process screenshot: {e}"
                    else: result = f"Failed to take screenshot: {path if path else 'Unknown error'}"
                elif command == "find": result = file_controller.find_file(params.get("filename", ""))
                elif command == "search": result = file_controller.find_file(params.get("query", ""))
                elif command == "list": result = file_controller.list_directory(params.get("path"))
                elif command == "disk": result = file_controller.get_disk_space()
                elif command == "downloads": result = file_controller.get_downloads()
                elif command == "get": 
                    path = file_controller.get_file(params.get("path", ""))
                    if path and not path.startswith("❌"):
                        try:
                            with open(path, "rb") as f:
                                encoded_string = base64.b64encode(f.read()).decode('utf-8')
                            result = f"File {os.path.basename(path)} fetched"
                            self.sio.emit('command_result', {'output': result, 'image_data': encoded_string}) # Server treats image_data as generic media if needed
                            return 
                        except Exception as e:
                            result = f"Failed to fetch file: {e}"
                    else: result = f"Failed: {path}"

            # --- SHELL COMMANDS ---
            elif action == "shell":
                if command == "execute": result = shell_controller.execute_command(params.get("command", ""))
    
            # --- INPUT COMMANDS (REMOTE ACCESS) ---
            elif action == "input":
                if command == "click":
                    result = input_controller.click(x=params.get("x"), y=params.get("y"), button=params.get("button", "left"))
                elif command == "type":
                    result = input_controller.type_text(params.get("text", ""))
                elif command == "press":
                    result = input_controller.press_key(params.get("key", ""))
                elif command == "hotkey":
                    result = input_controller.hotkey(*params.get("keys", []))
                elif command == "move":
                    result = input_controller.move_to(params.get("x", 0), params.get("y", 0))
                elif command == "info":
                    result = input_controller.get_screen_info()
                elif command == "live":
                    # Take screenshot and return it
                    path = file_controller.take_screenshot()
                    if path and not path.startswith("❌"):
                        try:
                            with open(path, "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                            result = "Updated view"
                            self.sio.emit('command_result', {'output': result, 'image_data': encoded_string})
                            return 
                        except: result = "Failed to process view"
                    else: result = "Failed to capture view"

            # --- BROWSER COMMANDS ---
            elif action == "browser":
                if command == "open_url": result = browser_controller.open_url(params.get("url", ""))
                elif command == "search_google": result = browser_controller.search_google(params.get("query", ""))
                elif command == "search_youtube": result = browser_controller.search_youtube(params.get("query", ""))
                elif command == "youtube": result = browser_controller.open_youtube()
                elif command == "gmail": result = browser_controller.open_gmail()
                elif command == "meet": result = browser_controller.open_google_meet()
                elif command == "github": result = browser_controller.open_github()
                elif command == "close": result = browser_controller.close_browser()
                elif command == "new_tab": result = browser_controller.new_tab(params.get("url"))
                elif command == "open_youtube": result = browser_controller.open_youtube()
                elif command == "search":
                     if "youtube" in str(params).lower(): result = browser_controller.search_youtube(params.get("query", ""))
                     else: result = browser_controller.search_google(params.get("query", ""))
    
            # --- MEDIA COMMANDS ---
            elif action == "media":
                if command == "play_pause": result = media_controller.play_pause()
                elif command == "next": result = media_controller.next_track()
                elif command == "prev": result = media_controller.prev_track()
                elif command == "now_playing": result = media_controller.get_now_playing()
    
            else:
                result = f"Unknown action: {action}"
    
        except Exception as e:
            result = f"Error executing command: {str(e)}"
            
        self.log(f"📤 Result: {result}")
        self.sio.emit('command_result', {'output': result})


def main():
    print("🤖 Nexus Agent")
    print("-------------------------")
    
    SERVER_URL = "http://localhost:5002"
    print(f"Target Server: {SERVER_URL}")
    code = input("Enter Pairing Code (from WhatsApp): ")
    
    client = AgentClient(SERVER_URL)
    client.connect(code)
    
    # Keep alive for CLI
    client.sio.wait()

if __name__ == "__main__":
    main()
