#!/bin/bash
PATH=$PATH:/usr/local/bin/
#=====================================================
# Script Name: start_session.sh
# Description: This script creates a new tmux session
#              and executes the backend start script for
#              chatAmeritas application.
# Author: Koushik Sinha
# Date: 9/10/2024
# Version: 1.1
#=====================================================

# Get the directory of the currently running script
BACKEND_PATH=$(dirname "$(realpath "$0")")
mkdir -p "$BACKEND_PATH/logs"

# Define the name of the tmux session
SESSION_NAME="Ameritasgpt-session"

# Define the start script's path within the backend directory
START_SCRIPT="$BACKEND_PATH/start.sh"

# Locate tmux binary
TMUX_BIN="$(command -v tmux)"
if [ -z "$TMUX_BIN" ]; then
  echo "Error: tmux not found in PATH." >&2
  exit 1
fi

# Check if the tmux session is already running
if $TMUX_BIN has-session -t $SESSION_NAME 2>/dev/null; then
  echo "The tmux session '$SESSION_NAME' is already running."
else
  if [ ! -x "$START_SCRIPT" ]; then
    echo "Error: start script '$START_SCRIPT' is not executable." >&2
    exit 1
  fi
  echo [$(date '+%Y-%m-%d %H:%M:%S')] "Starting a new tmux session: $SESSION_NAME"

  # Create a new tmux session and run the start script
  $TMUX_BIN new-session -d -s $SESSION_NAME /bin/bash -c "cd $BACKEND_PATH && $START_SCRIPT">> $BACKEND_PATH/logs/start_session.log 2>&1
  # Set a hook to log when the session closes
  $TMUX_BIN set-hook -t $SESSION_NAME session-closed "run-shell 'echo [\$(date)] Session $SESSION_NAME closed >> $BACKEND_PATH/logs/session_hook.log'"

  # Notify that the session has started
  echo [$(date '+%Y-%m-%d %H:%M:%S')] "Tmux session '$SESSION_NAME' created and start script executed."
fi
