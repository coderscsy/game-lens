#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  printf 'Python 3.10 or newer is required for live data.\nOpen steam_lens.html to use the offline demo.\n'
  exit 1
fi
exec python3 server.py
