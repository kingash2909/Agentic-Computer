
import os
import sys
import threading
import webbrowser
import time
from flask import Flask, render_template_string, request, jsonify

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.run_agent import AgentClient

app = Flask(__name__)

# Config Path
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".server_url")

def get_server_url():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f: return f.read().strip()
        except: pass
    return "http://localhost:5002"

def save_server_url(url):
    with open(CONFIG_PATH, "w") as f: f.write(url)

AGENT_HUB_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus Agent Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: white; margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .hub-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); padding: 2.5rem; border-radius: 24px; border: 1px solid rgba(255,255,255,0.1); width: 450px; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
        .logo { font-size: 2rem; margin-bottom: 1.5rem; display: block; }
        h2 { margin-bottom: 0.5rem; }
        p { color: #94a3b8; margin-bottom: 2rem; font-size: 0.9rem; }
        input { width: 100%; padding: 12px; border-radius: 12px; border: 1px solid #334155; background: #1e293b; color: white; margin-bottom: 1rem; outline: none; transition: border 0.2s; }
        input:focus { border-color: #22d3ee; }
        .btn { width: 100%; padding: 14px; border-radius: 12px; border: none; background: #22d3ee; color: #083344; font-weight: 700; cursor: pointer; transition: transform 0.2s, background 0.2s; }
        .btn:hover { background: #67e8f9; transform: translateY(-2px); }
        #status { margin-top: 1.5rem; padding: 10px; border-radius: 8px; font-size: 0.85rem; display: none; }
        .paired { background: rgba(16, 185, 129, 0.2); color: #10b981; }
    </style>
</head>
<body>
    <div class="hub-card">
        <span class="logo">🤖</span>
        <h2>Nexus Agent Hub</h2>
        <p>Your computer's remote interface.</p>
        
        <input type="text" id="server_url" placeholder="Server URL (e.g. https://xyz.render.com)" value="{{ server_url }}">
        <input type="text" id="pair_code" placeholder="Enter Pairing Code from WhatsApp">
        
        <button class="btn" onclick="connectAgent()">Launch & Connect</button>
        
        <div id="status"></div>
        
        <div style="margin-top:2rem; font-size:12px; color:#475569">
            After connecting, you can control this laptop from the <a href="{{ server_url }}" target="_blank" style="color:#22d3ee">Main Dashboard</a>.
        </div>
    </div>

    <script>
        function connectAgent() {
            const url = document.getElementById('server_url').value;
            const code = document.getElementById('pair_code').value;
            const status = document.getElementById('status');
            
            if(!code) return alert("Please enter a pairing code!");
            
            status.style.display = 'block';
            status.innerText = "🔄 Connecting to " + url + "...";
            status.className = '';

            fetch('/api/connect', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url, code})
            })
            .then(r => r.json())
            .then(data => {
                if(data.status === 'ok') {
                    status.innerText = "🎉 Agent successfully paired and online!";
                    status.classList.add('paired');
                    setTimeout(() => window.open(url, '_blank'), 2000);
                } else {
                    status.innerText = "❌ Error: " + data.message;
                }
            });
        }
    </script>
</body>
</html>
"""

client = None

@app.route('/')
def index():
    return render_template_string(AGENT_HUB_HTML, server_url=get_server_url())

@app.route('/api/connect', methods=['POST'])
def connect_api():
    global client
    data = request.json
    url = data.get('url', '').strip().rstrip('/')
    code = data.get('code', '').strip()
    
    save_server_url(url)
    
    if client: client.disconnect()
    
    # Initialize real agent client
    # Since we're in a separate route, we should handle logs via printing or queue
    client = AgentClient(server_url=url)
    
    # Start connection in thread
    t = threading.Thread(target=client.connect, args=(code,))
    t.daemon = True
    t.start()
    
    # Wait longer for status check (Render can be slow)
    for _ in range(10):
        if client.sio.connected: break
        time.sleep(1)
    
    if client.sio.connected:
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to connect. Check URL and Code.'})

def run_flask():
    app.run(port=5003, debug=False, use_reloader=False)

if __name__ == "__main__":
    print("🚀 Starting Nexus Agent Hub UI on http://localhost:5003")
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(1)
    webbrowser.open("http://localhost:5003")
    
    # Keep main thread alive
    while True:
        time.sleep(1)
