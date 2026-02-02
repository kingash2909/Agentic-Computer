"""
Intent Parser - Uses Groq AI to understand natural language commands
Parses user messages and returns structured actions
"""

from groq import Groq
import json
import config

# Initialize Groq client
client = Groq(api_key=config.GROQ_API_KEY)

# System prompt for command parsing
SYSTEM_PROMPT = """You are a command parser for a computer control bot. 
Analyze the user's message and determine what action they want to perform.

Return a JSON object with:
- "action": one of [system, app, file, browser, chat]
- "command": the specific command
- "params": any parameters needed


IMPORTANT: Return ONLY valid JSON, no other text.

Examples:
User: "open chrome" -> {"action": "app", "command": "open", "params": {"app_name": "chrome"}}
User: "battery" -> {"action": "system", "command": "battery", "params": {}}
User: "find file.txt" -> {"action": "file", "command": "find", "params": {"filename": "file.txt"}}
User: "search youtube cat videos" -> {"action": "browser", "command": "search_youtube", "params": {"query": "cat videos"}}

Context: You may be provided with previous messages. Use them to resolve references like "it", "that", "open it", etc.
"""


def parse_intent(user_message, history=None):
    """
    Parse user message and return structured command
    Returns: dict with action, command, and params
    """
    if history is None:
        history = []
        
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add history to messages
    for msg in history[-5:]:  # Keep last 5 turns for context
        messages.append(msg)
        
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.1,  # Low temperature for consistent parsing
            max_tokens=200
        )
        
        result = response.choices[0].message.content.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        result = result.strip()
        
        # Parse JSON
        parsed = json.loads(result)
        return parsed
        
    except json.JSONDecodeError:
        # If parsing fails, treat as chat
        return {
            "action": "chat",
            "command": "respond",
            "params": {"message": user_message}
        }
    except Exception as e:
        print(f"Intent parsing error: {e}")
        return {
            "action": "chat",
            "command": "respond",
            "params": {"message": user_message}
        }


def get_chat_response(message, history=None):
    """Get a conversational response from Groq"""
    if history is None:
        history = []
        
    messages = [
        {"role": "system", "content": "You are a helpful assistant integrated into a WhatsApp bot. Keep responses concise and friendly. Use emojis occasionally."}
    ]
    
    # Add history
    for msg in history[-5:]:
        messages.append(msg)
        
    messages.append({"role": "user", "content": message})
    
    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Sorry, I couldn't process that. Error: {str(e)}"
