#!/bin/bash
echo "🛑 Stopping all containers..."

# Use the appropriate docker-compose command
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.doug.yml down
else
    docker compose -f docker-compose.doug.yml down
fi

echo "✅ All stopped!"
