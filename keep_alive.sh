#!/bin/bash
# Keep Codespace alive by preventing idle timeout
# Runs a ping every 5 minutes to keep the session active
while true; do
    curl -s -o /dev/null http://localhost:8000/health
    sleep 300
done
