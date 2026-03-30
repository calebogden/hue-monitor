#!/usr/bin/env python3
"""
Interactive setup for Hue Monitor.
Discovers bridge, pairs, and configures sensors.
"""

import sys
import time
from bridge import discover_bridges, create_application_key, list_sensors_with_names
from config import (
    load_config, save_config, set_bridge, add_sensor, 
    get_bridge_ip, get_bridge_key, set_telegram
)


def setup_bridge():
    """Discover and pair with Hue Bridge."""
    print("\n🔍 Discovering Hue bridges on your network...")
    bridges = discover_bridges()
    
    if not bridges:
        print("❌ No Hue bridges found. Make sure your bridge is connected to the network.")
        return False
    
    if len(bridges) == 1:
        bridge = bridges[0]
        print(f"✅ Found bridge: {bridge['internalipaddress']}")
    else:
        print(f"Found {len(bridges)} bridges:")
        for i, b in enumerate(bridges):
            print(f"  {i + 1}. {b['internalipaddress']}")
        
        choice = input("Select bridge number: ").strip()
        try:
            bridge = bridges[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return False
    
    bridge_ip = bridge['internalipaddress']
    
    # Check if we already have a key for this bridge
    existing_ip = get_bridge_ip()
    existing_key = get_bridge_key()
    
    if existing_ip == bridge_ip and existing_key:
        print(f"✅ Already paired with this bridge.")
        use_existing = input("Use existing credentials? (Y/n): ").strip().lower()
        if use_existing != 'n':
            return True
    
    # Pair with bridge
    print(f"\n👆 Press the button on your Hue bridge, then press Enter here...")
    input()
    
    print("Pairing with bridge...")
    key = create_application_key(bridge_ip)
    
    if key:
        set_bridge(bridge_ip, key)
        print(f"✅ Successfully paired with bridge!")
        return True
    else:
        print("❌ Failed to pair with bridge. Make sure you pressed the button.")
        return False


def setup_sensors():
    """Select sensors to monitor."""
    bridge_ip = get_bridge_ip()
    bridge_key = get_bridge_key()
    
    if not bridge_ip or not bridge_key:
        print("❌ Bridge not configured. Run bridge setup first.")
        return False
    
    print("\n🚪 Fetching door/window sensors...")
    sensors = list_sensors_with_names(bridge_ip, bridge_key)
    
    if not sensors:
        print("❌ No contact sensors found. Make sure you have a Hue door/window sensor.")
        return False
    
    print(f"\nFound {len(sensors)} sensor(s):")
    for i, sensor in enumerate(sensors):
        status = "🟢 closed" if sensor['state'] == 'closed' else "🔴 open"
        print(f"  {i + 1}. {sensor['name']} ({status})")
    
    print("\nEnter sensor numbers to monitor (comma-separated), or 'all':")
    choice = input("> ").strip().lower()
    
    if choice == 'all':
        selected = sensors
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected = [sensors[i] for i in indices]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return False
    
    for sensor in selected:
        add_sensor(sensor['id'], sensor['name'])
        print(f"✅ Added: {sensor['name']}")
    
    return True


def setup_telegram():
    """Configure Telegram notifications."""
    print("\n📱 Telegram Notification Setup")
    print("To use Telegram notifications, you need:")
    print("  1. A Telegram bot token (from @BotFather)")
    print("  2. Your Telegram chat ID")
    
    enable = input("\nEnable Telegram notifications? (y/N): ").strip().lower()
    if enable != 'y':
        return
    
    bot_token = input("Bot token: ").strip()
    chat_id = input("Chat ID: ").strip()
    
    if bot_token and chat_id:
        set_telegram(bot_token, chat_id)
        print("✅ Telegram configured!")
    else:
        print("❌ Invalid input, skipping Telegram setup.")


def main():
    print("=" * 50)
    print("  Hue Monitor Setup")
    print("=" * 50)
    
    # Step 1: Bridge setup
    if not setup_bridge():
        sys.exit(1)
    
    # Step 2: Sensor setup
    if not setup_sensors():
        sys.exit(1)
    
    # Step 3: Notifications
    setup_telegram()
    
    print("\n" + "=" * 50)
    print("  Setup Complete!")
    print("=" * 50)
    print("\nRun 'python3 monitor.py' to start monitoring.")
    print("Logs will be saved to ~/.hue-monitor/logs/")


if __name__ == "__main__":
    main()
