#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/.env"
exec "$DIR/venv/bin/python" "$DIR/main.py"
