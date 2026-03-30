# Hue Monitor Memory

## Project Overview
Desktop app and service for monitoring Philips Hue door/window sensors with push notifications.

- **GitHub:** https://github.com/calebogden/hue-monitor
- **Slack:** #feat-hue-monitor (C0AQ1RHLLE5)
- **Notion:** https://www.notion.so/Hue-Monitor-333f0c263ebf81a7af84e5225660cfc1
- **Local:** ~/dev/hue-monitor

## Architecture

### Components
- **CLI Monitor** (`src/monitor.py`): Python SSE listener connecting to Hue Bridge eventstream
- **Electron App** (`electron/`): Cross-platform desktop app with bridge pairing UI (scaffold complete, needs icons)
- **Health Check** (`scripts/ensure-running.sh`): Cron-based watchdog with network pre-check

### Event Flow (Real-time, <1 second)
```
Door opens → Hue Bridge detects → SSE push → monitor.py receives → Telegram API → Notification
```

### Config Storage
- `~/.hue-monitor/config.json` — Bridge credentials, sensor list, notification settings
- `~/.hue-monitor/monitor.pid` — Current monitor PID (for single-instance)
- `~/.hue-monitor/logs/` — monitor.log, ensure.log, events.log

## Current Deployment (Mac Studio)

**Running via cron health check:**
```
*/5 * * * * /Users/co/dev/hue-monitor/scripts/ensure-running.sh
```

**Check status:**
```bash
ssh studio "ps aux | grep monitor.py | grep -v grep"
ssh studio "tail -20 ~/.hue-monitor/logs/monitor.log"
ssh studio "cat ~/.hue-monitor/monitor.pid"
```

**Manual restart:**
```bash
ssh studio "pkill -9 -f monitor.py; ~/dev/hue-monitor/scripts/ensure-running.sh"
```

## Credentials
- **Bridge IP:** 192.168.100.122
- **Bridge App Key:** Rq9RvB4Ao6h9MWaUqp2gCq9NBecPXbcygC5305dS
- **Sensor ID:** 56de0e85-8395-48f0-89eb-0cc03f5d7476 ("Bedroom Door")
- **Telegram Bot Token:** 8656201990:AAEXFPeXng4MlTjME5kk6Eo-rjG5Ub2YypE
- **Telegram Chat ID:** 6817707385 (Caleb)

## Lessons Learned

### launchd/cron Network Timing (2026-03-30)
**Problem:** Processes spawned by launchd/cron failed with "No route to host" even though network was available.

**Root Cause:** Early-spawned daemon processes may start before network routing table is fully initialized. The kernel returns EHOSTUNREACH because it can't find a route.

**Solution:** 
1. Network pre-check with curl retry loop before starting monitor
2. PID file for reliable single-instance management
3. Health monitoring that checks for "Connected!" in recent logs
4. Auto-kill and restart unhealthy processes

**Key insight:** curl works from cron (network IS available), but timing matters. Always pre-check before starting long-running network services.

## Remaining Work

### Phase 2: Electron App
- [ ] Add icons (icns, ico, png for tray)
- [ ] Test bridge pairing flow end-to-end
- [ ] Build and test on macOS
- [ ] Native macOS notifications (in addition to Telegram)

### Phase 3: Distribution
- [ ] Apple Developer account setup
- [ ] Code signing and notarization
- [ ] App Store metadata and screenshots
- [ ] Sandboxing considerations (network access, keychain for credentials)

### Features (Backlog)
- [ ] Multiple sensor support in UI
- [ ] Notification sound customization  
- [ ] Menu bar icon with connection status
- [ ] Event history view
- [ ] "Door left open" alerts (time threshold)
