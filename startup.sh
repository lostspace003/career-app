#!/bin/bash

# Startup script for Azure App Service
echo "Starting AI Tech Career Path Finder..."

# Install dependencies
echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Start Gunicorn with Uvicorn workers
echo "Starting Gunicorn server..."
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
