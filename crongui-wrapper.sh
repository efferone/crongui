#!/bin/bash
# Wrapper script for crongui

# do we have permissions? or use pkexec
if [ "$(id -u)" -ne 0 ]; then
    echo "CronGUI needs elevated privileges to edit crontabs"
    exec pkexec "$0" "$@"
fi

# run the actual app
exec python3 "$SNAP/bin/crongui.py" "$@"
