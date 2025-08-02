#!/usr/bin/env bash
APP_MODULE="$1"
HOST="$2"
PORT="$3"
LOG_LVL="$4"
LOG_CONFIG="$5"
WORKERS="$6"

# Ensure uvicorn command exists
if ! command -v uvicorn >/dev/null 2>&1; then
  echo "Error: uvicorn command not found. Please install uvicorn and ensure it is in your PATH." >&2
  exit 1
fi

# Validate the application module argument
if [ "$APP_MODULE" != "open_webui.main:app" ]; then
  echo "Error: first argument must be 'open_webui.main:app'." >&2
  exit 1
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
LOGS_DIR="$SCRIPT_DIR/logs"
CRASH_LOG="$LOGS_DIR/app_crash.log"

mkdir -p "$LOGS_DIR"

extra_args=""
if [ -n "$LOG_LVL" ]; then
  extra_args="--log-level $LOG_LVL"
fi
if [ -n "$LOG_CONFIG" ]; then
  extra_args="$extra_args --log-config $LOG_CONFIG"
fi

echo "Self recovery enabled: the server will restart if it exits unexpectedly"
while true; do
  WEBUI_SECRET_KEY="$WEBUI_SECRET_KEY" \
    uvicorn "$APP_MODULE" \
      --host "$HOST" \
      --port "$PORT" \
      --forwarded-allow-ips '*' \
      $extra_args \
      --access-log \
      --workers "$WORKERS"
  exit_code=$?
  ts=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$ts] Uvicorn exited with status $exit_code, restarting in 5 seconds..." | tee -a "$CRASH_LOG" >&2
  sleep 5
done
