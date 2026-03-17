#!/usr/bin/env bash
#
#  start.sh – Start FIWARE Smart Store (Práctica 2)
#  1. Start Docker Compose (Orion + MongoDB + tutorial)
#  2. Wait for Orion to be healthy
#  3. Load initial data (import-data)
#  4. Start Flask + SocketIO application
#
set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

export FLASK_PORT=${FLASK_PORT:-5000}
export ORION_URL=${ORION_URL:-http://localhost:1026/v2}

echo "🐳 Starting Docker Compose..."
docker compose up -d

echo "⏳ Waiting for Orion Context Broker..."
until curl -s http://localhost:1026/version > /dev/null 2>&1; do
  sleep 2
  printf "."
done
echo " ✅ Orion ready"

echo "📦 Loading initial data into Orion..."
docker run --rm \
  -v "$REPO_DIR/import-data:/import-data" \
  --network fiware_default \
  --entrypoint /bin/ash \
  quay.io/curl/curl /import-data
echo " ✅ Data loaded"

echo "🚀 Starting Flask application on port $FLASK_PORT ..."
# Activate venv if present
if [ -d "$REPO_DIR/.venv" ]; then
  source "$REPO_DIR/.venv/bin/activate"
fi
python3 app.py
