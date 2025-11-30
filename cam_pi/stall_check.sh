#!/bin/bash
# Specify the directory to search
DIRECTORY="/home/pi/capture"
AGE_LIMIT=1200

# Find the oldest file in the directory tree
NEWEST_FILE=$(find "$DIRECTORY" -type f -printf '%T+ %p\n' | sort -r | head -n 1 | cut -d' ' -f2-)

# Check if an oldest file was found
if [[ -n "$NEWEST_FILE" ]]; then
    # Get the age of the oldest file in seconds
    FILE_AGE=$(($(date +%s) - $(date +%s -r "$NEWEST_FILE")))

    # Check if the file is older than 20 minutes (1200 seconds)
    if [[ "$FILE_AGE" -gt $AGE_LIMIT ]]; then
        reboot
    fi
fi