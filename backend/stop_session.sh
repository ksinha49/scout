#!/bin/bash

#=====================================================
# Script Name: stop_session.sh
# Description: This script terminates a tmux session
#              if it is running.
# Author: Koushik Sinha
# Date: 9/11/2024
# Version: 1.0
#=====================================================

# Specify the path to the tmux executable (usually /usr/bin/tmux)
TMUX_EXECUTABLE="/bin/tmux"
# Define the name of the tmux session
SESSION_NAME="Ameritasgpt-session"

# Check if the tmux session is running
if $TMUX_EXECUTABLE has-session -t $SESSION_NAME 2>/dev/null; then
  echo [$(date '+%Y-%m-%d %H:%M:%S')] "The tmux session '$SESSION_NAME' is running. Terminating it..."
  
  # Kill the tmux session
  $TMUX_EXECUTABLE kill-session -t $SESSION_NAME
  pkill -f "gunicorn"
  # Notify that the session has been terminated
  echo [$(date '+%Y-%m-%d %H:%M:%S')] "Tmux session '$SESSION_NAME' has been terminated."
else
  echo [$(date '+%Y-%m-%d %H:%M:%S')] "No tmux session named '$SESSION_NAME' is running."
fi
