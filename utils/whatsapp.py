"""
WhatsApp Utilities - Send messages and media via WhatsApp Cloud API
"""

import requests
import os
import config


def send_message(to_number, text):
    """Send a text message via WhatsApp"""
    url = f"https://graph.facebook.com/v17.0/{config.PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WA_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"📤 Sent to {to_number} | Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False


def send_image(to_number, image_path, caption=None):
    """Send an image via WhatsApp (requires uploading to Meta first)"""
    try:
        # First, upload the image to Meta
        upload_url = f"https://graph.facebook.com/v17.0/{config.PHONE_NUMBER_ID}/media"
        headers = {"Authorization": f"Bearer {config.WA_TOKEN}"}
        
        with open(image_path, 'rb') as image_file:
            files = {
                'file': (os.path.basename(image_path), image_file, 'image/png'),
                'type': (None, 'image/png'),
                'messaging_product': (None, 'whatsapp')
            }
            upload_response = requests.post(upload_url, headers=headers, files=files)
        
        if upload_response.status_code != 200:
            print(f"❌ Failed to upload image: {upload_response.text}")
            return False
        
        media_id = upload_response.json().get('id')
        
        # Now send the message with the uploaded media
        send_url = f"https://graph.facebook.com/v17.0/{config.PHONE_NUMBER_ID}/messages"
        headers["Content-Type"] = "application/json"
        
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "image",
            "image": {
                "id": media_id,
                "caption": caption or "📸 Screenshot"
            }
        }
        
        response = requests.post(send_url, headers=headers, json=data)
        print(f"📸 Sent image to {to_number} | Status: {response.status_code}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Failed to send image: {e}")
        return False

def download_media(media_id):
    """
    Download media file from WhatsApp
    
    Args:
        media_id (str): WhatsApp Media ID
        
    Returns:
        str: Path to saved file or None
    """
    try:
        # 1. Get Media URL
        url = f"https://graph.facebook.com/v17.0/{media_id}"
        headers = {"Authorization": f"Bearer {config.WA_TOKEN}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to get media URL: {response.text}")
            return None
            
        media_url = response.json().get('url')
        mime_type = response.json().get('mime_type')
        
        # Determine extension
        ext = ".ogg"  # Default for voice notes
        if "audio/mpeg" in mime_type:
            ext = ".mp3"
        elif "audio/mp4" in mime_type:
            ext = ".m4a"
            
        # 2. Download File
        media_response = requests.get(media_url, headers=headers)
        if media_response.status_code != 200:
            print(f"❌ Failed to download media content")
            return None
            
        # Save to temp file
        filename = f"temp_{media_id}{ext}"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'wb') as f:
            f.write(media_response.content)
            
        print(f"📥 Downloaded media to {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Error downloading media: {e}")
        return None
