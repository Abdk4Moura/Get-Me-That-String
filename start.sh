#!/bin/bash
nohup python ./core/server.py --config config.ini > server.log 2>&1 &
echo "Server Started, check logs in /path/to/your/project/server.log"