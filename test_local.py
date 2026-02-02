"""
Local Tester - Test your Agentic Computer without WhatsApp
Simulates receiving messages and executing commands.
"""

import time
# Mock config and imports
import config
from ai.intent_parser import parse_intent
from app import execute_command

def test_command(message):
    print(f"\n🙋 User says: '{message}'")
    
    try:
        print("🧠 Thinking...")
        intent = parse_intent(message)
        print(f"🎯 Intent Detected: {intent}")
        
        print("⚡ Executing...")
        result = execute_command(intent)
        
        print(f"🤖 Bot Reply: {result}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Agentic Computer - Local Test Mode")
    print("-------------------------------------")
    print(f"🔑 Using Groq API Key: {config.GROQ_API_KEY[:5]}...")
    
    # List of tests to run
    # Comment out ones you don't want to run immediately
    tests = [
        "what's my battery?",
        "volume 20",
        "mute",
        "unmute",
        "search google for agentic ai",
        "open calculator"  # Try to find an app or fallback
    ]
    
    while True:
        user_input = input("\n⌨️  Enter a command (or 'exit' to quit): ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        test_command(user_input)
