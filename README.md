# Hue Monitor

Monitor Philips Hue door/window sensors and get instant notifications when they open.

## Features

- Real-time SSE event stream from Hue Bridge (no polling)
- Push notifications via Telegram, Slack, or native macOS
- Event logging with timestamps
- Auto-reconnect on connection drops
- Electron app for easy setup (coming soon)

## Quick Start (CLI)

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run setup to pair with your Hue Bridge
python3 src/setup.py

# Start monitoring
python3 src/monitor.py
```

## Electron App

Coming soon — a native macOS/Windows/Linux app with:
- Bridge auto-discovery
- One-click pairing
- Sensor selection UI
- Notification preferences
- Menu bar integration

## Requirements

- Philips Hue Bridge (v2)
- Hue door/window contact sensor
- Python 3.9+ (for CLI)
- Node.js 18+ (for Electron app)

## License

MIT
