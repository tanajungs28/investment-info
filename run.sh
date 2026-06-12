#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
source "$DIR/.env"

# Firestore 永続化用のサービスアカウント鍵（gitignore 済み）。
# 存在すれば読み込む。project_id は JSON から main.py が自動取得する。
SA_FILE="$DIR/config/firebase-service-account.json"
if [ -f "$SA_FILE" ]; then
  export FIREBASE_SERVICE_ACCOUNT="$(cat "$SA_FILE")"
fi

exec "$DIR/venv/bin/python" "$DIR/main.py"
