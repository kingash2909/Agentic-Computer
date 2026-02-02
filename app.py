"""
Agentic Computer - WhatsApp Controlled System Bot
Main Flask application that routes WhatsApp commands to appropriate controllers
"""

from flask import Flask, request
import config
import os

# Import controllers
from controllers import system_controller, app_controller, file_controller, browser_controller, media_controller
from ai.intent_parser import parse_intent, get_chat_response
from utils.whatsapp import send_message, send_image, download_media
from ai.audio import transcribe_audio

app = Flask(__name__)

# Store conversation history: {phone_number: [{"role": "user", "content": "msg"}, ...]}
CONVERSATIONS = {}


# ==========================================
# COMMAND ROUTER
# ==========================================

def execute_command(intent):
    """Execute command based on parsed intent"""
    action = intent.get("action")
    command = intent.get("command")
    params = intent.get("params", {})
    
    # --- SYSTEM COMMANDS ---
    if action == "system":
        if command == "shutdown":
            return system_controller.shutdown()
        elif command == "restart":
            return system_controller.restart()
        elif command == "sleep":
            return system_controller.sleep()
        elif command == "lock":
            return system_controller.lock_screen()
        elif command == "volume":
            level = params.get("level", 50)
            return system_controller.set_volume(level)
        elif command == "mute":
            return system_controller.mute()
        elif command == "unmute":
            return system_controller.unmute()
        elif command == "battery":
            return system_controller.get_battery()
        elif command == "info":
            return system_controller.get_system_info()
        elif command == "brightness":
            level = params.get("level", 50)
            return system_controller.set_brightness(level)
    
    # --- APP COMMANDS ---
    elif action == "app":
        if command == "open":
            app_name = params.get("app_name", "")
            return app_controller.open_app(app_name)
        elif command == "close":
            app_name = params.get("app_name", "")
            return app_controller.close_app(app_name)
        elif command == "list":
            return app_controller.list_running_apps()
        elif command == "switch":
            app_name = params.get("app_name", "")
            return app_controller.switch_to_app(app_name)
        elif command == "kill":
            app_name = params.get("app_name", "")
            return app_controller.kill_app(app_name)
        elif command == "current":
            return app_controller.get_frontmost_app()
    
    # --- FILE COMMANDS ---
    elif action == "file":
        if command == "screenshot":
            return "SCREENSHOT"  # Special handling in webhook
        elif command == "find":
            filename = params.get("filename", "")
            return file_controller.find_file(filename)
        elif command == "list":
            path = params.get("path")
            return file_controller.list_directory(path)
        elif command == "disk":
            return file_controller.get_disk_space()
        elif command == "downloads":
            return file_controller.get_downloads()
    
    # --- BROWSER COMMANDS ---
    elif action == "browser":
        if command == "open_url":
            url = params.get("url", "")
            return browser_controller.open_url(url)
        elif command == "search_google":
            query = params.get("query", "")
            return browser_controller.search_google(query)
        elif command == "search_youtube":
            query = params.get("query", "")
            return browser_controller.search_youtube(query)
        elif command == "youtube":
            return browser_controller.open_youtube()
        elif command == "gmail":
            return browser_controller.open_gmail()
        elif command == "meet":
            return browser_controller.open_google_meet()
        elif command == "github":
            return browser_controller.open_github()
        elif command == "close":
            return browser_controller.close_browser()
        elif command == "new_tab":
            url = params.get("url")
            return browser_controller.new_tab(url)

    # --- MEDIA COMMANDS ---
    elif action == "media":
        if command == "play_pause":
            return media_controller.play_pause()
        elif command == "next":
            return media_controller.next_track()
        elif command == "prev":
            return media_controller.prev_track()
        elif command == "now_playing":
            return media_controller.get_now_playing()
    
    # --- CHAT (Default) ---
    elif action == "chat":
        message = params.get("message", "")
        return get_chat_response(message)
    
    return "🤔 I didn't understand that command. Try something like 'open chrome' or 'what's my battery?'"


# ==========================================
# WEBHOOK ROUTES
# ==========================================

@app.route('/webhook', methods=['GET'])
def verify():
    """Verify webhook for Meta"""
    if request.args.get("hub.verify_token") == config.VERIFY_TOKEN:
        print("✅ Webhook verified!")
        return request.args.get("hub.challenge")
    return "Error", 403


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages"""
    data = request.json
    
    try:
        # Check if this is a message
        if data['entry'][0]['changes'][0]['value'].get('messages'):
            message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
            phone_no = message_data['from'].replace('+', '')
            msg_type = message_data.get('type')
            
            # Get history
            if phone_no not in CONVERSATIONS:
                CONVERSATIONS[phone_no] = []
            
            history = CONVERSATIONS[phone_no]
            
            user_text = ""
            
            # 1. Handle Voice Notes (Audio)
            if msg_type == 'audio':
                print(f"🎤 Received audio from {phone_no}")
                audio_id = message_data['audio']['id']
                
                # Download
                audio_path = download_media(audio_id)
                if audio_path:
                    # Transcribe
                    user_text = transcribe_audio(audio_path)
                    print(f"📝 Transcribed: {user_text}")
                    
                    # Clean up file
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                else:
                    send_message(phone_no, "❌ Failed to download audio note.")
                    return "OK", 200

            # 2. Handle Text Messages
            elif msg_type == 'text':
                user_text = message_data['text']['body']
                print(f"📩 Received from {phone_no}: {user_text}")

            # Process if we have text (from directly typed or transcribed)
            if user_text:
                # Add to history
                history.append({"role": "user", "content": user_text})
                
                # Parse intent with history
                intent = parse_intent(user_text, history)
                print(f"🎯 Intent: {intent}")
                
                # Execute command
                if intent['action'] == 'chat':
                    # Special handling for chat to use history
                    response_text = get_chat_response(user_text, history)
                    response = response_text
                else:
                    response = execute_command(intent)
                
                # Handle screenshot specially (need to send image)
                if response == "SCREENSHOT":
                    screenshot_path = file_controller.take_screenshot()
                    if screenshot_path:
                        send_image(phone_no, screenshot_path, "📸 Here's your screenshot!")
                        send_message(phone_no, "✅ Screenshot captured!")
                        history.append({"role": "assistant", "content": "Screenshot captured"})
                    else:
                        send_message(phone_no, "❌ Failed to take screenshot")
                        history.append({"role": "assistant", "content": "Failed to take screenshot"})
                else:
                    # Send text response
                    send_message(phone_no, str(response))
                    history.append({"role": "assistant", "content": str(response)})
                
                # Truncate history if too long
                if len(history) > 10:
                    CONVERSATIONS[phone_no] = history[-10:]
                
    except Exception as e:
        print(f"❌ Error: {e}")
        
    return "OK", 200


@app.route('/', methods=['GET'])
def home():
    """Home route for testing"""
    return """
    <h1>🖥️ Agentic Computer</h1>
    <p>WhatsApp-controlled system bot is running!</p>
    <h3>Supported Commands:</h3>
    <ul>
        <li>🔋 "battery" - Check battery status</li>
        <li>📱 "open chrome" - Launch apps</li>
        <li>❌ "close spotify" - Close apps</li>
        <li>📋 "what apps are running" - List apps</li>
        <li>📸 "screenshot" - Take screenshot</li>
        <li>🔍 "find resume.pdf" - Search files</li>
        <li>🌐 "open youtube.com" - Open URLs</li>
        <li>🔎 "search google for weather" - Web search</li>
        <li>🔊 "volume 50" - Adjust volume</li>
        <li>🔒 "lock" - Lock screen</li>
        <li>💾 "disk space" - Check storage</li>
    </ul>
    """


# ==========================================
# MAIN
# ==========================================

if __name__ == '__main__':
    print("🖥️ Agentic Computer starting...")
    print(f"📡 Server running on port {config.PORT}")
    print("💡 Use ngrok to expose: ngrok http 5002")
    app.run(port=config.PORT, debug=config.DEBUG)
