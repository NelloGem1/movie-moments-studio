#!/bin/bash
cd ~/youtube-tool/assets
source ~/venv/bin/activate
pkill -f scheduled_publisher.py 2>/dev/null
sleep 2
echo "Starting Movie Moments Scheduled Publisher..."
nohup python3 scheduled_publisher.py > scheduled_publisher.log 2>&1 &
Publisher_PID=$!
echo $Publisher_PID > ~/.movie_publisher.pid
echo "Publisher started with PID: $Publisher_PID"
echo "Logs: ~/youtube-tool/assets/scheduled_publisher.log"
echo "To stop: kill $(cat ~/.movie_publisher.pid)"
