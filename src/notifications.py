"""
Notification handlers for various platforms.
"""

import subprocess
import sys
import requests
from typing import Optional
from datetime import datetime


def send_telegram(bot_token: str, chat_id: str, message: str) -> bool:
    """Send a Telegram notification."""
    if not bot_token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram notification failed: {e}")
        return False


def send_slack(webhook_url: str, message: str) -> bool:
    """Send a Slack notification via webhook."""
    if not webhook_url:
        return False
    
    payload = {"text": message}
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Slack notification failed: {e}")
        return False


def send_native_notification(title: str, message: str) -> bool:
    """Send a native macOS notification."""
    if sys.platform != "darwin":
        return False
    
    script = f'''
    display notification "{message}" with title "{title}"
    '''
    
    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"Native notification failed: {e}")
        return False


def format_door_message(sensor_name: str, state: str, timestamp: Optional[datetime] = None) -> str:
    """Format a door event message."""
    if timestamp is None:
        timestamp = datetime.now()
    
    time_str = timestamp.strftime("%H:%M:%S")
    emoji = "🚪" if state == "open" else "🔒"
    action = "opened" if state == "open" else "closed"
    
    return f"{emoji} {sensor_name} {action} at {time_str}"


def format_door_message_html(sensor_name: str, state: str, timestamp: Optional[datetime] = None) -> str:
    """Format a door event message with HTML (for Telegram)."""
    if timestamp is None:
        timestamp = datetime.now()
    
    time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    emoji = "🚪" if state == "open" else "🔒"
    action = "opened" if state == "open" else "closed"
    
    return f"{emoji} <b>{sensor_name}</b> {action} at {time_str}"
