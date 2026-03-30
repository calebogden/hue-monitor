#!/bin/bash
# Start hue-monitor in a tmux session
export PATH="/opt/homebrew/bin:$PATH"
cd "$(dirname "$0")/.."
/opt/homebrew/bin/tmux kill-session -t hue-monitor 2>/dev/null || true
sleep 2
/opt/homebrew/bin/tmux new-session -d -s hue-monitor "cd $(pwd)/src && $(pwd)/venv/bin/python monitor.py"
