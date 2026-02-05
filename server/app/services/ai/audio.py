"""
Audio Processing Module
Uses Groq's Whisper integration to transcribe audio files
"""

from groq import Groq
import config
import os

# Initialize Groq client
client = Groq(api_key=config.GROQ_API_KEY)

def transcribe_audio(audio_path):
    """
    Transcribe audio file using Groq (Whisper)
    
    Args:
        audio_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    try:
        if not os.path.exists(audio_path):
            return ""

        with open(audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), file.read()),
                model="whisper-large-v3",
                response_format="text"
            )
        
        return str(transcription).strip()
    
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return ""
