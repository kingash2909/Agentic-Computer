
import customtkinter as ctk
import threading
import sys
import os

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.run_agent import AgentClient

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AgentGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Nexus Agent")
        self.geometry("600x500")
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="🤖 Nexus Agent", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(self.header_frame, text="Status: Disconnected", text_color="red")
        self.status_label.pack(pady=(0, 10))

        # Connection Frame
        self.connect_frame = ctk.CTkFrame(self)
        self.connect_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.url_label = ctk.CTkLabel(self.connect_frame, text="Server URL:")
        self.url_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.url_entry = ctk.CTkEntry(self.connect_frame, width=250)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)
        self.url_entry.insert(0, "http://localhost:5002")
        
        self.code_label = ctk.CTkLabel(self.connect_frame, text="Pairing Code:")
        self.code_label.grid(row=1, column=0, padx=10, pady=10)
        
        self.code_entry = ctk.CTkEntry(self.connect_frame, width=100)
        self.code_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        self.connect_btn = ctk.CTkButton(self.connect_frame, text="Connect", command=self.start_connection)
        self.connect_btn.grid(row=2, column=0, columnspan=2, padx=10, pady=20)

        # Log Frame
        self.log_textbox = ctk.CTkTextbox(self, width=500, height=200)
        self.log_textbox.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.log_textbox.insert("0.0", "--- Logs will appear here ---\n")
        self.log_textbox.configure(state="disabled")

        # Client Logic
        self.client = None
        
    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def update_status(self, status):
        if status == "connected":
            self.status_label.configure(text="Status: Connected", text_color="orange") # Socket connected, waiting for pair
        elif status == "paired":
            self.status_label.configure(text="Status: Paired & Online", text_color="green")
            self.connect_btn.configure(state="disabled", text="Connected")
        elif status == "disconnected":
            self.status_label.configure(text="Status: Disconnected", text_color="red")
            self.connect_btn.configure(state="normal", text="Connect")

    def start_connection(self):
        url = self.url_entry.get()
        code = self.code_entry.get()
        
        if not code:
            self.log("⚠️ Please enter a pairing code.")
            return

        self.connect_btn.configure(state="disabled", text="Connecting...")
        
        # Initialize Client
        if self.client:
            self.client.disconnect()
            
        self.client = AgentClient(
            server_url=url,
            on_log=self.log,
            on_status_change=self.update_status
        )
        
        # Run in thread to not block UI
        t = threading.Thread(target=self.client.connect, args=(code,))
        t.daemon = True
        t.start()
        
    def on_closing(self):
        if self.client:
            self.client.disconnect()
        self.destroy()

if __name__ == "__main__":
    app = AgentGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
