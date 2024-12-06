#!/bin/bash


# Start Quart app (quart_cam_feed.py) in the background
echo "Starting Quart app..."
python3 quart_cam_feed.py &

# Get the process ID of the Quart app
DASH_PID=$!

sleep 8

# Start Dash app (app.py) in the background
echo "Starting Dash app..."
python3 app.py &

# Get the process ID of the Dash app
QUART_PID=$!

# Wait for a short duration to allow the apps to initialize
sleep 3

# Open the default browser to the Dash app URL
echo "Opening browser to http://localhost:8050..."
xdg-open "http://localhost:8050" || open "http://localhost:8050"

# Wait for both apps to run and allow for termination with CTRL+C
echo "Press CTRL+C to terminate both apps."
wait $DASH_PID $QUART_PID

# Cleanup in case of termination
echo "Terminating apps..."
kill $DASH_PID $QUART_PID 2>/dev/null