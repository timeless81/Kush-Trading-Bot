#!/bin/bash
# Kill any existing server on 8080
pkill -f "python3 -m http.server 8080" 2>/dev/null
sleep 0.5

# Start server from the bot folder
cd "$(dirname "$0")"
python3 -m http.server 8080 &
sleep 1

# Open in Safari
open -a Safari "http://localhost:8080/bot.html"
echo "Bot running at http://localhost:8080/bot.html"
echo "Press Ctrl+C to stop the server."
wait
