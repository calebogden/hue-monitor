"""
Heartbeat module for dead man's switch monitoring.
Pings Healthchecks.io to confirm the monitor is alive.
"""

import os
import threading
import time
import requests

# Get ping URL from environment or config
HEALTHCHECKS_URL = os.environ.get("HEALTHCHECKS_URL", "")

def send_heartbeat():
    """Send a single heartbeat ping."""
    if not HEALTHCHECKS_URL:
        return False
    try:
        requests.get(HEALTHCHECKS_URL, timeout=10)
        return True
    except:
        return False

def start_heartbeat_thread(interval_seconds=300):
    """Start background thread that pings every N seconds."""
    if not HEALTHCHECKS_URL:
        print("[Heartbeat] No HEALTHCHECKS_URL configured, skipping", flush=True)
        return None
    
    def heartbeat_loop():
        while True:
            try:
                requests.get(HEALTHCHECKS_URL, timeout=10)
                print(f"[Heartbeat] Ping sent", flush=True)
            except Exception as e:
                print(f"[Heartbeat] Failed: {e}", flush=True)
            time.sleep(interval_seconds)
    
    thread = threading.Thread(target=heartbeat_loop, daemon=True)
    thread.start()
    print(f"[Heartbeat] Started (every {interval_seconds}s) -> {HEALTHCHECKS_URL[:50]}...", flush=True)
    return thread
