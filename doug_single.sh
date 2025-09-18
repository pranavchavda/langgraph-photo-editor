#!/bin/bash
if [ $# -eq 0 ]; then
    echo "Usage: ./doug_single.sh <image-file> [instructions]"
    echo "Example: ./doug_single.sh photo.jpg 'make it more vibrant'"
    exit 1
fi

IMAGE="$1"
INSTRUCTIONS="${2:-enhance and optimize}"

# Copy image to input folder
cp "$IMAGE" ./input/

# Use the appropriate docker-compose command
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py process "/data/input/$(basename $IMAGE)" --instructions "$INSTRUCTIONS" --output-dir /data/output
else
    docker compose -f docker-compose.doug.yml run --rm photo-editor python photo_editor.py process "/data/input/$(basename $IMAGE)" --instructions "$INSTRUCTIONS" --output-dir /data/output
fi

echo "✅ Done! Check ./output folder"
