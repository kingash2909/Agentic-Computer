"""
Shell Controller - Handles arbitrary command execution for remote access
"""

import subprocess
import os

def execute_command(command_str):
    """Execute a shell command and return output"""
    try:
        # Using shell=True allows for piped commands, but be careful
        # We use a 10 second timeout to prevent hanging
        result = subprocess.run(
            command_str, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=10,
            env={**os.environ, 'LANG': 'en_US.UTF-8'}
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if not output and not error:
            return "✅ Command executed (no output)."
            
        combined = []
        if output:
            combined.append(f"📤 Output:\n{output}")
        if error:
            combined.append(f"⚠️ Error/Stderr:\n{error}")
            
        return "\n\n".join(combined)
        
    except subprocess.TimeoutExpired:
        return "⏱️ Command timed out after 10 seconds."
    except Exception as e:
        return f"❌ Failed to execute command: {str(e)}"
