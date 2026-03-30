# AGENTS.md - Hue Monitor

This is the workspace for the Hue Monitor project — a desktop app for monitoring Philips Hue door/window sensors.

## Session Initialization

On every session start, load ONLY these files:
1. `memory/MEMORY.md` — project context and current state
2. `memory/YYYY-MM-DD.md` — today's daily notes (if exists)

**Run memory health check early:**
```bash
ls -la memory/
```

**End of session:** Update `memory/YYYY-MM-DD.md` with what you worked on.

## Project Structure

```
hue-monitor/
├── src/                  # Python CLI monitor
│   ├── monitor.py        # Main SSE listener
│   ├── bridge.py         # Hue Bridge API
│   ├── config.py         # Config management
│   ├── notifications.py  # Notification handlers
│   └── setup.py          # Interactive setup
├── electron/             # Desktop app
│   ├── main.js           # Electron main process
│   ├── index.html        # UI
│   └── assets/           # Icons (need to add)
├── scripts/              # Deployment scripts
│   ├── ensure-running.sh # Cron health check
│   └── start-delayed.sh  # Startup script
├── memory/               # Agent memory
└── venv/                 # Python virtualenv
```

## Key Files

- **Config location:** `~/.hue-monitor/config.json`
- **Logs:** `~/.hue-monitor/logs/`
- **Event log:** `~/.hue-monitor/logs/events.log`

## Deployment

Currently running on Mac Studio:
- Cron job: `*/5 * * * * ~/dev/hue-monitor/scripts/ensure-running.sh`
- Check status: `ssh studio "ps aux | grep monitor.py"`
- View logs: `ssh studio "tail -20 ~/.hue-monitor/logs/monitor.log"`

## Commands

```bash
# Test monitor locally
cd src && ../venv/bin/python monitor.py

# Run setup wizard
cd src && ../venv/bin/python setup.py

# Build Electron app
cd electron && npm install && npm run build:mac

# Check Mac Studio status
ssh studio "ps aux | grep monitor.py | grep -v grep"
```

## Links

- GitHub: https://github.com/calebogden/hue-monitor
- Slack: #feat-hue-monitor
- Notion: https://www.notion.so/Hue-Monitor-333f0c263ebf81a7af84e5225660cfc1
