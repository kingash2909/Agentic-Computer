# ===========================================
# AGENTIC COMPUTER - CONFIGURATION
# ===========================================

import os

# WhatsApp Cloud API Configuration
# Get these from Meta Developer Dashboard: https://developers.facebook.com/
WA_TOKEN = os.getenv("WA_TOKEN", "your_token_here")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "your_phone_id_here")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "your_verify_token")  # You create this - must match in Meta Dashboard

# Groq AI Configuration (Fast & Free!)
# Get from: https://console.groq.com/keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_key_here")
GROQ_MODEL = "llama-3.3-70b-versatile"  # Fast and powerful

# Server Configuration
PORT = 5002
DEBUG = True
