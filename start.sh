#!/bin/bash

# Startup script for BackendCloth API

echo "🚀 Starting BackendCloth API..."

# Check if we're in production (Render sets PORT environment variable)
if [ -n "$PORT" ]; then
    echo "🌐 Production mode detected, using gunicorn on port $PORT"
    exec gunicorn app.main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
else
    echo "🔧 Development mode detected, using uvicorn on port 8000"
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi 