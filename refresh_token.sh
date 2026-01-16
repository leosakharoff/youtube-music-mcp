#!/bin/bash
# Refresh YouTube Music MCP token and deploy to Render

set -e

cd "$(dirname "$0")"

echo "==> Starting YouTube OAuth flow..."
echo "y" | ./venv/bin/python -m src.auth

echo ""
echo "==> Encoding token to base64..."
TOKEN_B64=$(base64 < token.json | tr -d '\n')

echo "==> Updating token on Render..."
API_KEY=$(grep 'key:' ~/.render/cli.yaml | head -1 | awk '{print $2}')

curl -s -X PUT "https://api.render.com/v1/services/srv-d5jtober433s73ba12g0/env-vars/YOUTUBE_TOKEN_B64" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"value": "'"$TOKEN_B64"'"}' > /dev/null

echo "==> Triggering redeploy..."
curl -s -X POST "https://api.render.com/v1/services/srv-d5jtober433s73ba12g0/deploys" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" > /dev/null

echo ""
echo "Done! Token updated and deploy triggered."
echo "Check status: https://dashboard.render.com/web/srv-d5jtober433s73ba12g0"
