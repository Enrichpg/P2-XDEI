#!/usr/bin/env bash
#  stop.sh – Stop FIWARE Smart Store Docker services
set -e
cd "$(dirname "$0")"
echo "🛑 Stopping Docker services..."
docker compose down
echo "✅ Done"
