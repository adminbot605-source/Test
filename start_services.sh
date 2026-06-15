#!/bin/bash
set -e

# Start Redis if not running
if ! redis-cli -h 127.0.0.1 ping > /dev/null 2>&1; then
    echo "Starting Redis..."
    redis-server --daemonize yes --logfile /tmp/redis.log --bind 127.0.0.1
    sleep 2
fi

echo "Redis: $(redis-cli -h 127.0.0.1 ping)"

# Run the bot
cd /home/runner/workspace/bot
exec python3 main.py
