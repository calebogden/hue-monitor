# Hue Monitor Memory

## Project Overview
Desktop app and service for monitoring Philips Hue door/window sensors with push notifications.

## Architecture
- **CLI Monitor** (`src/monitor.py`): Python SSE listener connecting to Hue Bridge eventstream
- **Electron App** (`electron/`): Cross-platform desktop app with bridge pairing UI (scaffold complete)
- **Config Storage**: `~/.hue-monitor/config.json` for bridge credentials and sensor preferences

## Current State (2026-03-30)
- CLI monitor working and deployed on Mac Studio
- Running via cron (`*/5 * * * *`) with `ensure-running.sh`
- Monitoring "Bedroom Door" sensor
- Telegram notifications working (to Caleb @ 6817707385)

## Credentials
- Bridge IP: 192.168.100.122
- Bridge Key: Rq9RvB4Ao6h9MWaUqp2gCq9NBecPXbcygC5305dS
- Sensor ID: 56de0e85-8395-48f0-89eb-0cc03f5d7476

## Remaining Work
1. **Electron App Completion**
   - Add proper icons (icns, ico, png)
   - Test bridge pairing flow in UI
   - Build and sign for distribution

2. **App Store Prep**
   - Apple Developer account setup
   - Code signing and notarization
   - App Store metadata and screenshots
   - Sandboxing considerations

3. **Features**
   - Multiple sensor support
   - Notification sound customization
   - Menu bar icon with status
   - Event history view
   - Native macOS notifications (in addition to Telegram)

## Artifacts
- GitHub: https://github.com/calebogden/hue-monitor
- Slack: #feat-hue-monitor (C0AQ1RHLLE5)
- Notion: https://www.notion.so/Hue-Monitor-333f0c263ebf81a7af84e5225660cfc1
- Local: ~/dev/hue-monitor
