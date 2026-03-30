#!/bin/bash
# Run health check on Mac Studio via SSH (SSH-spawned processes work reliably)
ssh studio '/Users/co/dev/hue-monitor/scripts/health-check.sh' 2>/dev/null
