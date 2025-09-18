#!/bin/bash
echo "🚀 Processing all images in ./input folder..."

# Use the appropriate docker-compose command
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py batch /data/input --output-dir /data/output
else
    docker compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py batch /data/input --output-dir /data/output
fi

echo "✅ Done! Check ./output folder for results"
