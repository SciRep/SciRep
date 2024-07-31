#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Create a dist folder
mkdir dist

# Copy static files
cp -r static dist/

# Copy templates
cp -r templates dist/

# Copy the Flask app
cp app.py dist/

# Create a custom start command for Azure
echo "gunicorn --bind=0.0.0.0 --timeout 600 app:app" > dist/start.sh
