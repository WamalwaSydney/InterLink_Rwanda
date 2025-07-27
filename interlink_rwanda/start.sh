#!/bin/bash

# Start Flask app in background
python3 app.py &

# Start WhatsApp bot
node bot.js
