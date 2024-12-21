# Description: Stop the server
# Usage: bash stop.sh [path]
# Example: bash stop.sh /home/user/Desktop/Server

DIR_PATH=$(pwd) # Default path
if [ -n "$1" ]; then
    DIR_PATH=$1
fi

if pkill -f "./core/server.py"; then
    echo "Server stopped successfully"
else
    echo "Server was not running"
fi