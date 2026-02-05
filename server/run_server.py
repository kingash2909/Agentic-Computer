
import eventlet
eventlet.monkey_patch()

import sys
import os
import random
import string

# Add root dir to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import services from server.app.services
from server.app.services.whatsapp import send_message, download_media, send_image
from server.app.services.ai.intent_parser import parse_intent, get_chat_response
from server.app.services.ai.audio import transcribe_audio

from flask import Flask, request, render_template_string
from flask_socketio import SocketIO, emit, join_room
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# Increase buffer size to 10MB to handle large screenshots
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10000000)

# In-memory stores
# PAIRING_CODES: { "1234": "phone_number" } - Temporary codes waiting for agent
# DEVICES: { "phone_number": "socket_id" } - Active connections maps phone to socket
# SESSIONS: { "socket_id": "phone_number" } - Reverse map
PAIRING_CODES = {}
DEVICES = {}
SESSIONS = {}
CONVERSATIONS = {}

# HTML for Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Nexus Control Center</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f9; }
        .container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .status-card { background: #e8f4fd; border-left: 5px solid #3498db; padding: 15px; margin-top: 20px; border-radius: 4px; }
        .instructions { background: #fff3e0; border-left: 5px solid #ff9800; padding: 15px; margin-top: 20px; border-radius: 4px; }
        code { background: #eee; padding: 2px 5px; border-radius: 3px; font-family: monospace; }
        ul { padding-left: 20px; }
        li { margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ Nexus Control Center</h1>
        
        <div class="status-card">
            <h3>Connected Devices: {{ devices_count }}</h3>
            {% if devices %}
                <ul>
                {% for phone, sid in devices.items() %}
                    <li>📱 <strong>{{ phone }}</strong> is connected (ID: <code>{{ sid[:8] }}...</code>)</li>
                {% endfor %}
                </ul>
            {% else %}
                <p>No devices currently connected.</p>
            {% endif %}
        </div>

        <div class="instructions">
            <h3>🚀 How to Connect Your Laptop</h3>
            <p>Render hosts the "Brain", but you must run the "Agent" locally on the laptop you want to control:</p>
            <ol>
                <li>Open a terminal on your <strong>laptop</strong>.</li>
                <li>Navigate to the project folder.</li>
                <li>Run <code>python agent/gui_app.py</code>.</li>
                <li>Enter this Server URL: <code>{{ request.url_root }}</code></li>
                <li>Send <strong>"Connect"</strong> to your WhatsApp bot to get a pairing code.</li>
            </ol>
        </div>
    </div>
</body>
</html>
"""

def generate_pairing_code():
    return ''.join(random.choices(string.digits, k=4))

# ==========================================
# SOCKET IO HANDLERS
# ==========================================

@socketio.on('connect')
def handle_connect():
    print(f"🔌 Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in SESSIONS:
        phone = SESSIONS[sid]
        print(f"🔌 Client disconnected: {sid} (User: {phone})")
        del SESSIONS[sid]
        if phone in DEVICES:
            del DEVICES[phone]

@socketio.on('register')
def handle_register(data):
    """mobile/user sends 'connect', gets code. Agent sends code here."""
    code = data.get('code')
    sid = request.sid
    
    # Find who owns this code
    # We need a way to look up pairing codes.
    # In this simple version, let's assume the pairing code is associated with a phone number
    # stored in PAIRING_CODES when the user requested it via WhatsApp.
    
    found_phone = None
    for c, p in PAIRING_CODES.items():
        if c == code:
            found_phone = p
            break
            
    if found_phone:
        print(f"✅ Device paired! User: {found_phone}, Socket: {sid}")
        DEVICES[found_phone] = sid
        SESSIONS[sid] = found_phone
        del PAIRING_CODES[code]
        
        emit('registration_success', {'status': 'ok'})
        
        welcome_msg = (
            "🤖 *Welcome to Nexus Agent!* 🤖\n\n"
            "✅ Your computer is now connected and ready to control.\n\n"
            "📱 *Available Commands:*\n"
            "• *System*: battery, info, volume [0-100], brightness [0-100], lock, sleep, restart, shutdown, clipboard\n"
            "• *Apps*: open [name], close [name], list, switch [name], current\n"
            "• *Files*: find [name], screenshot, disk space, downloads\n"
            "• *Browser*: open [url], search [query], youtube, gmail, meet, github\n"
            "• *Input*: click [x y], type [text], press [key], live\n"
            "• *Media*: play, next, prev, now playing\n\n"
            "💡 _Try saying 'screenshot' or 'what is my battery?'_"
        )
        send_message(found_phone, welcome_msg)
    else:
        print(f"❌ Invalid pairing code: {code}")
        emit('registration_failed', {'reason': 'Invalid code'})

@socketio.on('command_result')
def handle_result(data):
    """Result from agent execution"""
    content = data.get('output')
    image_data = data.get('image_data') # Base64 encoded image
    sid = request.sid
    
    if sid in SESSIONS:
        phone = SESSIONS[sid]
        
        # If we have an image, send it
        if image_data:
            import base64
            import time
             # Save to temp file
            filename = f"screenshot_{int(time.time())}.png"
            filepath = os.path.join(os.getcwd(), filename)
            
            try:
                with open(filepath, "wb") as fh:
                    fh.write(base64.b64decode(image_data))
                
                send_image(phone, filepath, "📸 Here is your screen")
                
                # Cleanup
                try: os.remove(filepath)
                except: pass
                
                # Add to history
                if phone in CONVERSATIONS:
                    CONVERSATIONS[phone].append({"role": "assistant", "content": "Sent a screenshot"})
                    
            except Exception as e:
                print(f"Error handling image: {e}")
                send_message(phone, "❌ Error processing screenshot")
        
        # Send text output if exists (and if not just confirming screenshot)
        elif content:
             send_message(phone, str(content))
        
             # Add to history
             if phone in CONVERSATIONS:
                  CONVERSATIONS[phone].append({"role": "assistant", "content": str(content)})


# ==========================================
# WHATSAPP WEBHOOK
# ==========================================

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == config.VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Error", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    try:
        if data['entry'][0]['changes'][0]['value'].get('messages'):
            msg_data = data['entry'][0]['changes'][0]['value']['messages'][0]
            phone_no = msg_data['from'].replace('+', '')
            msg_type = msg_data.get('type')
            
            # Init history
            if phone_no not in CONVERSATIONS: CONVERSATIONS[phone_no] = []
            history = CONVERSATIONS[phone_no]
            
            user_text = ""
            
            # Audio
            if msg_type == 'audio':
                print(f"🎤 Audio from {phone_no}")
                audio_path = download_media(msg_data['audio']['id'])
                if audio_path:
                    user_text = transcribe_audio(audio_path)
                    try: os.remove(audio_path) 
                    except: pass
            
            # Text
            elif msg_type == 'text':
                user_text = msg_data['text']['body']
                
            if user_text:
                print(f"📩 {phone_no}: {user_text}")
                history.append({"role": "user", "content": user_text})
                
                # Check for "Connect" command
                if "connect" in user_text.lower():
                    code = generate_pairing_code()
                    PAIRING_CODES[code] = phone_no
                    reply = (
                        "🔗 *Connection Requested!*\n\n"
                        "To control this computer, follows these steps on your laptop:\n\n"
                        "1️⃣ Run the Agent: `python agent/gui_app.py`\n"
                        "2️⃣ Enter this pairing code: *{}*\n"
                        "3️⃣ Make sure the Server URL is set to your Render URL.\n\n"
                        "⌛ This code will expire soon."
                    ).format(code)
                    send_message(phone_no, reply)
                    history.append({"role": "assistant", "content": reply})
                    return "OK", 200
                
                # Check if user has a connected device
                if phone_no not in DEVICES:
                    reply = "⚠️ No device connected. Type 'Connect' to pair your computer."
                    send_message(phone_no, reply)
                    history.append({"role": "assistant", "content": reply})
                    return "OK", 200
                
                # If connected, parse intent and forward to agent
                intent = parse_intent(user_text, history)
                print(f"🎯 Forwarding intent to agent: {intent}")
                
                target_sid = DEVICES[phone_no]
                
                if intent['action'] == 'chat':
                    # Chat happens on server (no need to bother agent)
                    resp = get_chat_response(user_text, history)
                    send_message(phone_no, resp)
                    history.append({"role": "assistant", "content": resp})
                else:
                    # Forward command to Agent
                    socketio.emit('execute_command', intent, room=target_sid)
                    
    except Exception as e:
        print(f"Error: {e}")
        
    return "OK", 200

@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML, devices=DEVICES, devices_count=len(DEVICES))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    print(f"📡 Server starting on port {port}...")
    # Host must be 0.0.0.0 for cloud deployment
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
