#!/bin/bash

#=====================================================
# Script Name: cleanup.sh
# Description: This script deletes all files in the
#              specified target directory and logs
#              the deletion process.
# Author: Koushik Sinha
# Date: 9/15/2024
# Version: 1.0
#=====================================================

# Get the directory where the script is located
SCRIPT_DIR=$(dirname "$0")

# Accepting the target directory and log file as arguments
TARGET_DIR=$1
LOG_FILE=$2

# Check if log file exists, if not create it
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

# Check if arguments are provided
if [ -z "$TARGET_DIR" ] || [ -z "$LOG_FILE" ]; then
    echo "Usage: $0 <target_directory> <log_file>"
    exit 1
fi

# Check if the target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Target directory $TARGET_DIR does not exist." | tee -a "$LOG_FILE"
    exit 1
fi

# Log the start of the cleanup process
echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting cleanup in $TARGET_DIR ." | tee -a "$LOG_FILE"

FILES=$(find "$TARGET_DIR" -type f)

if [ -z "$FILES" ]; then
      echo "[$(date +"%Y-%m-%d %H:%M:%S")]: No files found to delete." | tee -a "$LOG_FILE"
else
      echo "[$(date +"%Y-%m-%d %H:%M:%S")]: Listing files to be deleted:" | tee -a "$LOG_FILE"
      echo "$FILES" | tee -a "$LOG_FILE"

      # Delete the files after listing them
      find "$TARGET_DIR" -type f -exec rm {} \;

      echo "[$(date +"%Y-%m-%d %H:%M:%S")]: Deletion complete." | tee -a "$LOG_FILE"
fi
-1 -print | while read file; do
    echo "[$(date +"%Y-%m-%d %H:%M:%S")]: $file" | tee -a "$LOG_FILE"
done

# Exit successfully
exit 0
