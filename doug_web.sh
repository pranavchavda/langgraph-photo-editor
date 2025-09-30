#!/bin/bash
echo "🌐 Starting Photo Editor Web Interface..."
echo "Open your browser to: http://localhost:8501"
echo ""

# Use the appropriate docker-compose command with Doug's optimized config
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml up photo-editor
else
    docker compose -f docker-compose.doug.yml up photo-editor
fi
