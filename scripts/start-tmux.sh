#!/bin/bash
# Start hue-monitor in a tmux session
cd "$(dirname "$0")/.."
tmux kill-session -t hue-monitor 2>/dev/null || true
sleep 2
tmux new-session -d -s hue-monitor "cd src && ../venv/bin/python monitor.py"
