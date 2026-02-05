
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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus Unified Control Center</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        :root {
            --primary: #3498db;
            --secondary: #2ecc71;
            --danger: #e74c3c;
            --dark: #2c3e50;
            --light: #ecf0f1;
            --card-bg: #ffffff;
        }
        body { font-family: 'Inter', system-ui, -apple-system, sans-serif; background-color: #f0f2f5; margin: 0; padding: 0; display: flex; flex-direction: column; min-height: 100vh; }
        header { background: var(--dark); color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .container { flex: 1; padding: 2rem; max-width: 1200px; margin: 0 auto; width: 100%; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
        .card { background: var(--card-bg); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s; }
        .card:hover { transform: translateY(-3px); }
        .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 999px; font-size: 12px; font-weight: 600; }
        .badge-success { background: #d1fae5; color: #065f46; }
        .badge-warning { background: #fef3c7; color: #92400e; }
        .btn { padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; transition: background 0.2s; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-primary:hover { background: #2980b9; }
        .btn-outline { background: transparent; border: 1px solid #ddd; color: #666; }
        .btn-outline:hover { background: #f8f9fa; }
        .device-info { margin: 1rem 0; border-top: 1px solid #eee; padding-top: 1rem; }
        .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 1rem; }
        .log-panel { background: #1e1e1e; color: #d4d4d4; padding: 1rem; border-radius: 8px; font-family: 'Fira Code', monospace; height: 200px; overflow-y: auto; font-size: 12px; margin-top: 2rem; }
        .instructions { background: #fff8e1; border-left: 4px solid #ffc107; padding: 1rem; margin-bottom: 2rem; border-radius: 4px; }
        code { background: #eee; padding: 2px 4px; border-radius: 2px; }
    </style>
</head>
<body>
    <header>
        <h2 style="margin:0">🤖 Nexus Unified</h2>
        <div id="connection-status">
            <span class="badge badge-success">Dashboard Connected</span>
        </div>
    </header>

    <div class="container">
        <div class="instructions">
            <strong>🚀 Remote Setup:</strong> Run <code>python agent/gui_app.py</code> on your laptop. 
            Server URL: <code>{{ request.url_root }}</code>
        </div>

        <div class="grid">
            <div class="card">
                <h3>🖥️ Active Connections ({{ devices_count }})</h3>
                <div id="devices-list">
                    {% if devices %}
                        {% for phone, sid in devices.items() %}
                        <div class="device-info">
                            <div style="display:flex; justify-content:space-between; align-items:center">
                                <strong>📱 {{ phone[-4:] }}...{{ phone[-2:] }}</strong>
                                <span class="badge badge-success">Online</span>
                            </div>
                            <div class="controls">
                                <button class="btn btn-primary" onclick="sendCommand('{{ phone }}', 'screenshot')">📸 Screenshot</button>
                                <button class="btn btn-primary" onclick="sendCommand('{{ phone }}', 'battery')">🔋 Battery</button>
                                <button class="btn btn-outline" onclick="sendCommand('{{ phone }}', 'lock')">🔒 Lock</button>
                                <button class="btn btn-outline" onclick="sendCommand('{{ phone }}', 'info')">ℹ️ Info</button>
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p style="color:#666; font-style:italic">No agents connected. Pair a device via WhatsApp to start.</p>
                    {% endif %}
                </div>
            </div>

            <div class="card">
                <h3>💬 Last Activity</h3>
                <div id="activity-log" style="font-size:14px; color:#444">
                    Waiting for events...
                </div>
            </div>
        </div>

        <div class="log-panel" id="debug-log">
            [System] Dashboard initialized. Receiving live updates...
        </div>
    </div>

    <script>
        const socket = io();
        
        function sendCommand(phone, cmd) {
            log(`Triggering ${cmd} for ${phone}...`);
            socket.emit('web_command', { phone: phone, command: cmd });
        }

        function log(msg) {
            const panel = document.getElementById('debug-log');
            const time = new Date().toLocaleTimeString();
            panel.innerHTML += `\\n[${time}] ${msg}`;
            panel.scrollTop = panel.scrollHeight;
        }

        socket.on('log_update', (data) => {
            log(data.message);
            if (data.type === 'activity') {
                document.getElementById('activity-log').innerText = data.message;
            }
        });

        socket.on('command_result_web', (data) => {
            log(`Result: ${data.output}`);
        });
    </script>
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
        socketio.emit('log_update', {'message': f'❌ Failed pairing attempt with code {code}', 'type': 'system'})
        emit('registration_failed', {'reason': 'Invalid code'})

@socketio.on('web_command')
def handle_web_command(data):
    """Bridge command from browser dashboard to agent"""
    phone = data.get('phone')
    command = data.get('command')
    
    if phone in DEVICES:
        target_sid = DEVICES[phone]
        # Wrap into an intent-like object
        intent = {
            'action': 'system' if command in ['screenshot', 'battery', 'lock', 'info'] else 'unknown',
            'command': command,
            'params': {}
        }
        print(f"🌐 Web Dashboard triggering: {command} for {phone}")
        socketio.emit('execute_command', intent, room=target_sid)
        socketio.emit('log_update', {'message': f'🌐 Web trigger: {command}', 'type': 'activity'})
    else:
        emit('log_update', {'message': f'❌ Error: Device {phone} not connected'})

@socketio.on('command_result')
def handle_result(data):
    """Result from agent execution"""
    content = data.get('output')
    image_data = data.get('image_data') # Base64 encoded image
    sid = request.sid
    
    # Notify web dashboard
    socketio.emit('command_result_web', {'output': content})
    
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
                    print(f"🔑 Generated OTP {code} for {phone_no}")
                    socketio.emit('log_update', {'message': f'🔑 OTP Generated for {phone_no}', 'type': 'system'})
                    
                    reply = (
                        "🔗 *Connection Requested!*\n\n"
                        "To control this computer, follows these steps on your laptop:\n\n"
                        "1️⃣ Run the Agent: `python agent/gui_app.py`\n"
                        "2️⃣ Enter this pairing code: *{}*\n"
                        "3️⃣ Make sure the Server URL is set to your Render URL.\n\n"
                        "⌛ This code will expire soon."
                    ).format(code)
                    
                    success = send_message(phone_no, reply)
                    if not success:
                        print(f"‼️ FAILED to send WhatsApp response to {phone_no}")
                        socketio.emit('log_update', {'message': f'‼️ WhatsApp Send Failure to {phone_no}', 'type': 'error'})
                    
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
