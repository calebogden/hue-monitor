"""
Philips Hue Bridge API interactions.
"""

import json
import requests
import urllib3
from typing import Optional, List, Dict, Any

# Suppress SSL warnings (Hue bridge uses self-signed cert)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DISCOVERY_URL = "https://discovery.meethue.com"


def discover_bridges() -> List[Dict[str, str]]:
    """
    Discover Hue bridges on the network.
    Returns list of bridges with 'id' and 'internalipaddress'.
    """
    try:
        response = requests.get(DISCOVERY_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Bridge discovery failed: {e}")
        return []


def create_application_key(bridge_ip: str, app_name: str = "hue-monitor") -> Optional[str]:
    """
    Create an application key by pairing with the bridge.
    User must press the bridge button within 30 seconds before calling this.
    
    Returns the application key (username) on success, None on failure.
    """
    url = f"https://{bridge_ip}/api"
    payload = {
        "devicetype": f"{app_name}#monitor",
        "generateclientkey": True
    }
    
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            if "success" in data[0]:
                return data[0]["success"]["username"]
            elif "error" in data[0]:
                error = data[0]["error"]
                if error.get("type") == 101:
                    print("Error: Link button not pressed. Press the button on your Hue bridge and try again.")
                else:
                    print(f"Error: {error.get('description', 'Unknown error')}")
        return None
    except Exception as e:
        print(f"Failed to create application key: {e}")
        return None


def get_contact_sensors(bridge_ip: str, key: str) -> List[Dict[str, Any]]:
    """
    Get all contact sensors (door/window sensors) from the bridge.
    """
    url = f"https://{bridge_ip}/clip/v2/resource/contact"
    headers = {"hue-application-key": key}
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Failed to get contact sensors: {e}")
        return []


def get_device_info(bridge_ip: str, key: str, device_id: str) -> Optional[Dict[str, Any]]:
    """
    Get device information including name.
    """
    url = f"https://{bridge_ip}/clip/v2/resource/device/{device_id}"
    headers = {"hue-application-key": key}
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()
        devices = data.get("data", [])
        return devices[0] if devices else None
    except Exception as e:
        print(f"Failed to get device info: {e}")
        return None


def get_sensor_name(bridge_ip: str, key: str, sensor: Dict[str, Any]) -> str:
    """
    Get the friendly name of a sensor from its owner device.
    """
    owner = sensor.get("owner", {})
    device_id = owner.get("rid")
    
    if device_id:
        device = get_device_info(bridge_ip, key, device_id)
        if device:
            return device.get("metadata", {}).get("name", "Unknown Sensor")
    
    return "Unknown Sensor"


def list_sensors_with_names(bridge_ip: str, key: str) -> List[Dict[str, Any]]:
    """
    Get all contact sensors with their friendly names.
    """
    sensors = get_contact_sensors(bridge_ip, key)
    result = []
    
    for sensor in sensors:
        name = get_sensor_name(bridge_ip, key, sensor)
        state = sensor.get("contact_report", {}).get("state", "unknown")
        result.append({
            "id": sensor["id"],
            "name": name,
            "state": "closed" if state == "contact" else "open",
            "enabled": sensor.get("enabled", True),
        })
    
    return result
