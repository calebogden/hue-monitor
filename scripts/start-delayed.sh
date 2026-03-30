#!/bin/bash
# Wait for network to be fully ready, then start monitor
sleep 10
cd /Users/co/dev/hue-monitor/src
exec /Users/co/dev/hue-monitor/venv/bin/python monitor.py
