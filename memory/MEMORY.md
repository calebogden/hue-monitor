# Hue Monitor Memory

## Project Overview
Desktop app and service for monitoring Philips Hue door/window sensors with push notifications.

- **GitHub:** https://github.com/calebogden/hue-monitor
- **Slack:** #feat-hue-monitor (C0AQ1RHLLE5)  
- **Notion:** https://www.notion.so/Hue-Monitor-333f0c263ebf81a7af84e5225660cfc1
- **Local:** ~/dev/hue-monitor

## Current Deployment

**Primary: MacBook Pro (192.168.100.57)**
- Process: `~/dev/hue-monitor/venv/bin/python monitor.py`
- Logs: `~/.hue-monitor/logs/monitor.log`
- Auto-start: `~/Library/LaunchAgents/com.hue-monitor.plist`

**Mac Studio: UNRELIABLE — DO NOT USE**
- Python network connections fail from cron/launchd with "No route to host"
- SSH-spawned processes work, but that's not durable
- See daily notes for full investigation

## Quick Commands

```bash
# Check status
ps aux | grep monitor.py | grep -v grep
tail -20 ~/.hue-monitor/logs/monitor.log

# Restart
pkill -9 -f monitor.py
cd ~/dev/hue-monitor/src && nohup ../venv/bin/python monitor.py >> ~/.hue-monitor/logs/monitor.log 2>&1 &

# Check sensor state
curl -sk -H "hue-application-key: Rq9RvB4Ao6h9MWaUqp2gCq9NBecPXbcygC5305dS" \
  https://192.168.100.122/clip/v2/resource/contact | python3 -m json.tool
```

## Credentials
- **Bridge IP:** 192.168.100.122
- **Bridge Key:** Rq9RvB4Ao6h9MWaUqp2gCq9NBecPXbcygC5305dS
- **Sensor ID:** 56de0e85-8395-48f0-89eb-0cc03f5d7476 ("Bedroom Door")
- **Telegram Bot:** 8656201990:AAEXFPeXng4MlTjME5kk6Eo-rjG5Ub2YypE
- **Telegram Chat:** 6817707385 (Caleb)

## Known Issues

### 1. SSE Silent Death
**Problem:** SSE connection drops, `iter_lines()` hangs forever, no error logged.
**Solution:** 120-second read timeout in monitor.py — auto-reconnects if no data.

### 2. Mac Studio Network Failure (UNSOLVED)
**Problem:** Python can't connect to Hue bridge from cron/launchd context.
**Symptoms:** "No route to host" error, but curl/ping work fine.
**Workaround:** Run on MacBook instead.
**Status:** Unresolved — needs deeper investigation.

### 3. Duplicate Processes
**Problem:** Old launchd plists respawn monitors, causing duplicate notifications.
**Solution:** Always check for and remove stale launchd plists before deploying.

## Healthchecks.io (TODO)
Dead man's switch for network/monitor failure alerts.
- Sign up at healthchecks.io
- Create check with 5-min period, 5-min grace
- Set `HEALTHCHECKS_URL` environment variable
- Monitor will ping every 5 minutes
- If no ping for 10 min → SMS alert

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Hue Bridge                        │
│                  192.168.100.122                     │
│                                                      │
│  Door Sensor ──→ SSE eventstream ──→ monitor.py    │
└─────────────────────────────────────────────────────┘
                           │
                           │ Real-time push (<1s)
                           ▼
┌─────────────────────────────────────────────────────┐
│                    MacBook Pro                       │
│                  192.168.100.57                      │
│                                                      │
│  monitor.py ──→ Telegram API ──→ Caleb's phone     │
│       │                                              │
│       └──→ Healthchecks.io (TODO)                   │
└─────────────────────────────────────────────────────┘
```

## File Structure

```
~/dev/hue-monitor/
├── src/
│   ├── monitor.py      # Main SSE listener (120s timeout)
│   ├── heartbeat.py    # Healthchecks.io integration
│   ├── config.py       # Config file management
│   ├── bridge.py       # Hue Bridge API
│   ├── notifications.py # Telegram/native notifications
│   └── setup.py        # Interactive setup wizard
├── electron/           # Desktop app (scaffold)
├── scripts/
│   ├── ensure-running.sh
│   ├── health-check.sh
│   └── self-health-check.sh
├── memory/             # Agent memory
└── venv/               # Python virtualenv

~/.hue-monitor/
├── config.json         # Runtime config
├── monitor.pid         # Current PID
└── logs/
    ├── monitor.log     # Main output
    ├── events.log      # Door event history
    └── health.log      # Health check log
```
