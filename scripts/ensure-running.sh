#!/bin/bash
# Ensure hue-monitor is running (single instance, with network check)
set -e

PIDFILE="/Users/co/.hue-monitor/monitor.pid"
LOGFILE="/Users/co/.hue-monitor/logs/monitor.log"
BRIDGE_IP="192.168.100.122"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> /Users/co/.hue-monitor/logs/ensure.log
}

# Check if already running and healthy via pidfile
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        # Process exists - check if it's actually connected (not stuck in error loop)
        # Look for recent "Connected!" in last 20 lines of log
        RECENT_CONNECTED=$(tail -20 "$LOGFILE" 2>/dev/null | grep -c "Connected!" || echo 0)
        RECENT_ERRORS=$(tail -20 "$LOGFILE" 2>/dev/null | grep -c "Connection error" || echo 0)
        
        if [ "$RECENT_CONNECTED" -gt 0 ] && [ "$RECENT_ERRORS" -lt 5 ]; then
            # Healthy - exit
            exit 0
        else
            # Process exists but unhealthy - kill it
            log "Process $PID exists but unhealthy (connected=$RECENT_CONNECTED, errors=$RECENT_ERRORS), killing"
            kill -9 "$PID" 2>/dev/null || true
            sleep 2
        fi
    fi
fi

# Kill any stray instances
pkill -9 -f 'hue-monitor/src/monitor.py' 2>/dev/null || true
sleep 1

# Network pre-check: wait for bridge to be reachable (max 30s)
ATTEMPTS=0
MAX_ATTEMPTS=6
while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    if curl -sk --max-time 5 "https://$BRIDGE_IP/api/config" > /dev/null 2>&1; then
        log "Network check passed (attempt $((ATTEMPTS+1)))"
        break
    fi
    ATTEMPTS=$((ATTEMPTS+1))
    if [ $ATTEMPTS -eq $MAX_ATTEMPTS ]; then
        log "Network check failed after $MAX_ATTEMPTS attempts, aborting"
        exit 1
    fi
    log "Network check failed (attempt $ATTEMPTS), waiting 5s..."
    sleep 5
done

# Start the monitor
cd /Users/co/dev/hue-monitor/src
nohup /Users/co/dev/hue-monitor/venv/bin/python monitor.py >> "$LOGFILE" 2>&1 &
NEW_PID=$!
echo $NEW_PID > "$PIDFILE"
log "Started hue-monitor (PID $NEW_PID)"

# Wait a moment and verify it connected
sleep 5
if tail -5 "$LOGFILE" | grep -q "Connected!"; then
    log "Verified connected successfully"
else
    log "WARNING: Started but not yet connected, check logs"
fi
