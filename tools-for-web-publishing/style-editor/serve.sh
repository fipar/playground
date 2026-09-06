#!/usr/bin/env bash
# ==============================================================================
# StyleStudio - Local Server Launcher
# ==============================================================================

PORT=8080
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "--------------------------------------------------------"
echo "  🎨 Starting StyleStudio at http://localhost:${PORT}"
echo "--------------------------------------------------------"

# Check if python3 is available
if command -v python3 >/dev/null 2>&1; then
  echo "Serving with Python 3 http.server..."
  cd "$DIR" && python3 -m http.server "$PORT"
# Check if npx serve is available
elif command -v npx >/dev/null 2>&1; then
  echo "Serving with npx serve..."
  cd "$DIR" && npx serve -p "$PORT"
else
  echo "Neither python3 nor npx found. Please run any static HTTP server in:"
  echo "$DIR"
  exit 1
fi
