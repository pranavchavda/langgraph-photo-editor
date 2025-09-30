#!/bin/bash
echo "💬 Starting interactive chat mode..."

# Use the appropriate docker-compose command
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py chat
else
    docker compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py chat
fi
