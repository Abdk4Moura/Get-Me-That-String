#!/bin/bash

DIR_PATH=$(pwd) # Default path
if [ -n "$1" ]; then
    DIR_PATH=$1
fi
nohup python $DIR_PATH/core/server.py --config config.ini > server.log 2>&1 &
echo "Server Started, check logs in $DIR_PATH/server.log"