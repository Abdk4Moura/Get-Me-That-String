#!/bin/bash

DIR_PATH=$(pwd) # Default path
CONFIG_FILE="config" # Default config file

if command -v python3 &> /dev/null
then
    PYTHON_EXEC=$(which python3)
else
    PYTHON_EXEC=$(compgen -c | grep -E '^python3(\.[0-9]+)?$' | sort -V | tail -n 1)
    if [ -z "$PYTHON_EXEC" ]; then
        PYTHON_EXEC=$(command -v python || { echo "Python is not installed. Please install Python to proceed."; exit 1; })
    fi
fi

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --config) CONFIG_FILE="$2"; shift ;;
        *) DIR_PATH="$1" ;;
    esac
    shift
done

mkdir -p $DIR_PATH/logs

# main
LOG_FILE="$DIR_PATH/logs/server-$(date +'%Y%m%d%H%M%S').log"
nohup $PYTHON_EXEC $DIR_PATH/core/server.py --config $CONFIG_FILE > $LOG_FILE 2>&1 &
echo "Server Started, check logs in $LOG_FILE"

# delete log files older than 7 days
find $DIR_PATH/logs -type f -mtime +7 -delete
