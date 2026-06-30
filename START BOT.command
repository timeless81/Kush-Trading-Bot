#!/bin/bash
cd "$(dirname "$0")"

# Kill any existing server on port 8080
pkill -f "server.py" 2>/dev/null
pkill -f "python3 -m http.server 8080" 2>/dev/null
sleep 0.5

# Start the bot server (reads .env credentials automatically)
python3 server.py &
sleep 1

# Open in Safari
open -a Safari "http://localhost:8080/bot.html"
wait
