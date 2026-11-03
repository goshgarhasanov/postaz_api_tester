#!/usr/bin/env bash
# Postaz — MERN-style stack launcher
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "→ backend (Express) on :5177"
( cd "$ROOT/server" && PORT=5177 node src/index.js ) &
SRV=$!
echo "→ frontend (Vite) on :5173"
( cd "$ROOT/client" && npx vite --host ) &
WEB=$!
trap "kill $SRV $WEB 2>/dev/null" EXIT
echo "Open http://localhost:5173"
wait
