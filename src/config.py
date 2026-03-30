"""
Configuration management for Hue Monitor.
Stores bridge credentials and sensor preferences.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

CONFIG_DIR = Path.home() / ".hue-monitor"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "bridge": {
        "ip": None,
        "key": None,
    },
    "sensors": [],  # List of sensor IDs to monitor
    "notifications": {
        "telegram": {
            "enabled": False,
            "bot_token": None,
            "chat_id": None,
        },
        "slack": {
            "enabled": False,
            "webhook_url": None,
        },
        "native": {
            "enabled": True,  # macOS notifications
        },
    },
    "log_events": True,
}


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from disk."""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]):
    """Save configuration to disk."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_bridge_ip() -> Optional[str]:
    """Get configured bridge IP."""
    config = load_config()
    return config.get("bridge", {}).get("ip")


def get_bridge_key() -> Optional[str]:
    """Get configured bridge application key."""
    config = load_config()
    return config.get("bridge", {}).get("key")


def set_bridge(ip: str, key: str):
    """Set bridge IP and application key."""
    config = load_config()
    config["bridge"]["ip"] = ip
    config["bridge"]["key"] = key
    save_config(config)


def get_monitored_sensors() -> list:
    """Get list of sensor IDs to monitor."""
    config = load_config()
    return config.get("sensors", [])


def add_sensor(sensor_id: str, name: str):
    """Add a sensor to monitor."""
    config = load_config()
    # Store as dict with id and name
    sensor = {"id": sensor_id, "name": name}
    if sensor not in config["sensors"]:
        config["sensors"].append(sensor)
        save_config(config)


def remove_sensor(sensor_id: str):
    """Remove a sensor from monitoring."""
    config = load_config()
    config["sensors"] = [s for s in config["sensors"] if s.get("id") != sensor_id]
    save_config(config)


def set_telegram(bot_token: str, chat_id: str):
    """Configure Telegram notifications."""
    config = load_config()
    config["notifications"]["telegram"]["enabled"] = True
    config["notifications"]["telegram"]["bot_token"] = bot_token
    config["notifications"]["telegram"]["chat_id"] = chat_id
    save_config(config)


def get_telegram_config() -> Dict[str, Any]:
    """Get Telegram configuration."""
    config = load_config()
    return config.get("notifications", {}).get("telegram", {})
