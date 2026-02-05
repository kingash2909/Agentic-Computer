
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
# HTML for Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus Ultimate Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #22d3ee;
            --primary-glow: rgba(34, 211, 238, 0.4);
            --bg: #0f172a;
            --surface: rgba(30, 41, 59, 0.7);
            --border: rgba(255, 255, 255, 0.1);
            --text: #f1f5f9;
        }
        * { box-sizing: border-box; }
        body { 
            margin: 0; 
            font-family: 'Inter', sans-serif; 
            background: radial-gradient(circle at top left, #1e293b, #0f172a); 
            color: var(--text); 
            min-height: 100vh;
            overflow-x: hidden;
        }
        nav { 
            backdrop-filter: blur(10px); 
            background: rgba(15, 23, 42, 0.8); 
            border-bottom: 1px solid var(--border); 
            padding: 1rem 2rem; 
            position: sticky; top: 0; z-index: 100;
            display: flex; justify-content: space-between; align-items: center;
        }
        .logo { font-weight: 700; font-size: 1.5rem; color: var(--primary); display: flex; align-items: center; gap: 10px; }
        .container { max-width: 1400px; margin: 2rem auto; padding: 0 1rem; display: grid; grid-template-columns: 350px 1fr; gap: 2rem; }
        .card { 
            background: var(--surface); 
            backdrop-filter: blur(16px); 
            border: 1px solid var(--border); 
            border-radius: 20px; 
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .live-view-container { position: relative; width: 100%; aspect-ratio: 16/10; background: #000; border-radius: 12px; overflow: hidden; border: 2px solid var(--border); }
        .live-view-img { width: 100%; height: 100%; object-fit: contain; }
        .live-view-overlay { position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.6); padding: 5px 10px; border-radius: 5px; font-size: 12px; }
        .btn-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.8rem; margin-top: 1rem; }
        .btn { 
            background: rgba(255,255,255,0.05); 
            border: 1px solid var(--border); 
            color: white; padding: 0.8rem; border-radius: 10px; cursor: pointer;
            transition: all 0.2s; font-size: 0.9rem; font-weight: 600;
            display: flex; align-items: center; justify-content: center; gap: 8px;
        }
        .btn:hover { background: var(--primary); color: #000; transform: translateY(-2px); box-shadow: 0 0 15px var(--primary-glow); }
        .terminal { background: #000; border-radius: 12px; padding: 1rem; font-family: 'Fira Code', monospace; height: 250px; overflow-y: auto; font-size: 13px; border: 1px solid var(--border); }
        .terminal-input-row { display: flex; gap: 10px; margin-top: 1rem; }
        .terminal-input { flex: 1; background: rgba(0,0,0,0.5); border: 1px solid var(--border); color: var(--primary); padding: 8px 12px; border-radius: 6px; outline: none; }
    </style>
</head>
<body>
    <nav>
        <div class="logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
            NEXUS ULTIMATE
        </div>
        <div id="connection-status"><span style="color:#10b981">● Backend Live</span></div>
    </nav>

    <div class="container">
        <div class="sidebar">
            <div class="card">
                <h3 style="margin-top:0">📡 Connected</h3>
                <div id="devices-list">
                    {% if devices %}
                        {% for phone, sid in devices.items() %}
                        <div style="background:rgba(255,255,255,0.03); padding:1rem; border-radius:12px; border:1px solid var(--border); margin-bottom:1rem">
                            <strong>📱 {{ phone }}</strong>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p style="color:#64748b; font-style:italic">Waiting for agent...</p>
                    {% endif %}
                </div>
                <button class="btn" style="width:100%" onclick="simulateOTP()">🧪 Simulate OTP</button>
            </div>
                <h3 style="margin-top:0">🎮 Actions</h3>
                <div class="btn-grid">
                    <button class="btn" onclick="sendCommand('screenshot')">📸 Snap</button>
                    <button class="btn" onclick="sendStream('start')">📡 Go Live</button>
                    <button class="btn" onclick="sendStream('stop')">⏹️ Stop Live</button>
                    <button class="btn" onclick="sendCommand('battery')">🔋 Battery</button>
                    <button class="btn" onclick="sendCommand('lock')">🔒 Lock</button>
                    <button class="btn" onclick="sendCommand('info')">ℹ️ Info</button>
                </div>
        </div>

        <div class="main">
            <div class="card" style="padding:0; overflow:hidden">
                <div class="live-view-container">
                    <img id="live-screen" class="live-view-img" src="" onerror="this.src='https://via.placeholder.com/800x500?text=Waiting+for+Live+Stream...'">
                    <div class="live-view-overlay">LIVE STREAM • <span id="fps">0.0</span> FPS</div>
                </div>
            </div>
            <div class="card">
                <h3>📟 Activity Log</h3>
                <div class="terminal" id="web-log"></div>
                <div class="terminal-input-row">
                    <input type="text" id="shell-cmd" class="terminal-input" placeholder="Execute shell command...">
                    <button class="btn" onclick="executeShell()">Run</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let lastTime = Date.now();

        function log(msg, color='#d4d4d4') {
            const panel = document.getElementById('web-log');
            panel.innerHTML += `<div>[${new Date().toLocaleTimeString()}] <span style="color:${color}">${msg}</span></div>`;
            panel.scrollTop = panel.scrollHeight;
        }

        function sendCommand(cmd) {
            log(`Triggering ${cmd}...`, '#22d3ee');
            socket.emit('web_command', { command: cmd });
        }

        function sendStream(type) {
            log(`${type === 'start' ? 'Starting' : 'Stopping'} Live Stream...`, '#22d3ee');
            socket.emit('web_command', { command: type === 'start' ? 'start_live_view' : 'stop_live_view', action: 'stream' });
        }

        function executeShell() {
            const cmd = document.getElementById('shell-cmd').value;
            if (!cmd) return;
            socket.emit('web_command', { command: 'execute', action: 'shell', params: { command: cmd } });
            document.getElementById('shell-cmd').value = '';
        }

        function simulateOTP() {
            const num = prompt("Phone number:", "12345");
            if (num) socket.emit('simulate_whatsapp', { phone: num });
        }

        socket.on('log_update', (data) => log(data.message));
        socket.on('command_result_web', (data) => {
            if (data.image_data) {
                document.getElementById('live-screen').src = "data:image/png;base64," + data.image_data;
                const now = Date.now();
                document.getElementById('fps').innerText = (1000/(now - lastTime)).toFixed(1);
                lastTime = now;
            }
            if (data.output) log(data.output, '#f1f5f9');
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

@socketio.on('register_agent')
def handle_register(data):
    """mobile/user sends 'connect', gets code. Agent sends code here."""
    code = data.get('code')
    sid = request.sid
    
    print(f"🔑 Received registration attempt with code: {code}")
    
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
        socketio.emit('log_update', {'message': f'✅ Agent {found_phone} paired successfully', 'type': 'system'})
        
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
        socketio.emit('log_update', {'message': f'❌ Invalid pairing attempt with code: {code}', 'type': 'error'})
        emit('registration_failed', {'reason': 'Invalid code'})

@socketio.on('web_command')
def handle_web_command(data):
    """Bridge command from browser dashboard to agent"""
    phone = data.get('phone')
    command = data.get('command')
    action = data.get('action', 'system')
    params = data.get('params', {})
    
    if phone in DEVICES:
        target_sid = DEVICES[phone]
        
        # Stream commands (special handling)
        if action == 'stream':
            socketio.emit(command, {}, room=target_sid)
            return

        # Wrap into an intent-like object
        intent = {
            'action': action,
            'command': command,
            'params': params
        }
        print(f"🌐 Web Dashboard triggering: {command} for {phone}")
        socketio.emit('execute_command', intent, room=target_sid)
        socketio.emit('log_update', {'message': f'🌐 Web trigger: {command}', 'type': 'activity'})
    else:
        # If no phone specified but one exists, use the first one
        if not phone and DEVICES:
            phone = list(DEVICES.keys())[0]
            handle_web_command({'phone': phone, 'command': command, 'action': action, 'params': params})
        else:
            emit('log_update', {'message': f'❌ Error: Device not connected'})

@socketio.on('simulate_whatsapp')
def handle_simulation(data):
    """Simulate a WhatsApp 'connect' message for local testing"""
    phone_no = data.get('phone', 'test_user')
    print(f"🧪 Simulation: Received 'connect' from {phone_no}")
    
    code = generate_pairing_code()
    PAIRING_CODES[code] = phone_no
    
    msg = f"🔑 Simulation: Code generated for {phone_no} is {code}. Enter this in your local agent."
    print(msg)
    socketio.emit('log_update', {'message': f'🔑 Local Test: OTP {code} generated for {phone_no}', 'type': 'system'})
    # We don't call send_message here to avoid trying to hit Meta's API during simulation

@socketio.on('command_result')
def handle_result(data):
    """Result from agent execution"""
    content = data.get('output')
    image_data = data.get('image_data') # Base64 encoded image
    sid = request.sid
    
    # Notify web dashboard
    socketio.emit('command_result_web', {'output': content, 'image_data': image_data})
    
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
    return render_template_string(DASHBOARD_HTML, devices=DEVICES, devices_count=len(DEVICES), list=list)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    print(f"📡 Server starting on port {port}...")
    # Host must be 0.0.0.0 for cloud deployment
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
