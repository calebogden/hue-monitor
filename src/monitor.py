#!/usr/bin/env python3
"""
Hue Door Sensor Monitor
Connects to Hue Bridge SSE stream and sends notifications when doors open/close.
"""

import json
import socket
import requests
from requests.adapters import HTTPAdapter
import urllib3
from datetime import datetime
import sys
import time
import os
import threading
from pathlib import Path

from config import load_config, get_bridge_ip, get_bridge_key, get_telegram_config, CONFIG_DIR
from notifications import send_telegram, send_native_notification, format_door_message, format_door_message_html
from heartbeat import start_heartbeat_thread

# Suppress SSL warnings (Hue bridge uses self-signed cert)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOG_DIR = CONFIG_DIR / "logs"

# Watchdog: if no SSE data received in this many seconds, reconnect
SSE_TIMEOUT_SECONDS = 120  # Bridge sends heartbeat ": hi" roughly every 10s


class SourceAddressAdapter(HTTPAdapter):
    def __init__(self, source_address, **kwargs):
        self.source_address = source_address
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["source_address"] = (self.source_address, 0)
        super().init_poolmanager(*args, **kwargs)


def get_local_ip():
    """Get the local IP on the same network as the bridge."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.100.122", 443))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return None


def log_event(sensor_name: str, state: str, timestamp: str):
    """Log door event to file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "events.log"
    
    with open(log_file, "a") as f:
        f.write(f"{timestamp}\t{sensor_name}\t{state}\n")


def send_notifications(sensor_name: str, state: str):
    """Send notifications via all configured channels."""
    config = load_config()
    timestamp = datetime.now()
    
    # Telegram
    tg_config = config.get("notifications", {}).get("telegram", {})
    if tg_config.get("enabled"):
        message = format_door_message_html(sensor_name, state, timestamp)
        send_telegram(tg_config.get("bot_token"), tg_config.get("chat_id"), message)
    
    # Native macOS
    native_config = config.get("notifications", {}).get("native", {})
    if native_config.get("enabled"):
        title = "Hue Monitor"
        message = format_door_message(sensor_name, state, timestamp)
        send_native_notification(title, message)


def connect_and_monitor():
    """Connect to SSE stream and monitor for door events."""
    bridge_ip = get_bridge_ip()
    bridge_key = get_bridge_key()
    
    if not bridge_ip or not bridge_key:
        print("Error: Bridge not configured. Run setup.py first.", flush=True)
        sys.exit(1)
    
    config = load_config()
    monitored_sensors = {s["id"]: s["name"] for s in config.get("sensors", [])}
    
    if not monitored_sensors:
        print("Error: No sensors configured. Run setup.py to add sensors.", flush=True)
        sys.exit(1)
    
    # Get local IP for source binding
    local_ip = get_local_ip()
    print(f"[{datetime.now().isoformat()}] Local IP: {local_ip}", flush=True)
    
    # Start heartbeat for dead man's switch monitoring
    start_heartbeat_thread(interval_seconds=300)  # Every 5 minutes
    
    url = f"https://{bridge_ip}/eventstream/clip/v2"
    headers = {
        "hue-application-key": bridge_key,
        "Accept": "text/event-stream"
    }
    
    print(f"[{datetime.now().isoformat()}] Connecting to Hue Bridge SSE stream...", flush=True)
    print(f"[{datetime.now().isoformat()}] Monitoring {len(monitored_sensors)} sensor(s):", flush=True)
    for sensor_id, name in monitored_sensors.items():
        print(f"  - {name}", flush=True)
    
    # Track consecutive failures to recreate session
    consecutive_failures = 0
    session = None
    
    while True:
        # Create fresh session after 3 consecutive failures to recover from corrupted connection pool
        if consecutive_failures >= 3 or session is None:
            if consecutive_failures >= 3:
                print(f"[{datetime.now().isoformat()}] Creating fresh session after {consecutive_failures} failures", flush=True)
            session = requests.Session()
            if local_ip:
                adapter = SourceAddressAdapter(local_ip)
                session.mount("https://", adapter)
                session.mount("http://", adapter)
            consecutive_failures = 0
        
        last_data_time = time.time()
        
        try:
            # Use a read timeout to detect stale connections
            with session.get(url, headers=headers, stream=True, verify=False, timeout=(10, SSE_TIMEOUT_SECONDS)) as response:
                if response.status_code != 200:
                    print(f"[ERROR] Failed to connect: {response.status_code}", flush=True)
                    time.sleep(5)
                    continue
                
                print(f"[{datetime.now().isoformat()}] Connected!", flush=True)
                consecutive_failures = 0  # Reset on successful connection
                
                for line in response.iter_lines():
                    last_data_time = time.time()
                    
                    if not line:
                        continue
                    
                    line_str = line.decode("utf-8")
                    
                    # SSE heartbeat from Hue bridge
                    if line_str.startswith(": "):
                        continue  # Ignore SSE comments/heartbeats
                    
                    # SSE format: "data: <json>"
                    if not line_str.startswith("data: "):
                        continue
                    
                    json_str = line_str[6:]  # Strip "data: " prefix
                    
                    try:
                        events = json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
                    
                    # Process each event
                    for event in events:
                        if event.get("type") != "update":
                            continue
                        
                        for item in event.get("data", []):
                            if item.get("type") != "contact":
                                continue
                            
                            sensor_id = item.get("id")
                            if sensor_id not in monitored_sensors:
                                continue
                            
                            contact_report = item.get("contact_report", {})
                            state_raw = contact_report.get("state")
                            
                            if state_raw == "no_contact":
                                state = "open"
                            elif state_raw == "contact":
                                state = "closed"
                            else:
                                continue
                            
                            sensor_name = monitored_sensors[sensor_id]
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            print(f"[{timestamp}] {sensor_name}: {state.upper()}", flush=True)
                            
                            if config.get("log_events", True):
                                log_event(sensor_name, state.upper(), timestamp)
                            
                            if state == "open":
                                send_notifications(sensor_name, state)
        
        except requests.exceptions.ReadTimeout:
            print(f"[{datetime.now().isoformat()}] SSE read timeout (no data for {SSE_TIMEOUT_SECONDS}s), reconnecting...", flush=True)
            consecutive_failures += 1
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now().isoformat()}] Connection error: {e}", flush=True)
            consecutive_failures += 1
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Unexpected error: {e}", flush=True)
            consecutive_failures += 1
        
        print("Reconnecting in 5 seconds...", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    connect_and_monitor()
