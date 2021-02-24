#!/bin/bash
# Author: matt-hires
# Date: 12.12.20 14:01
# Description: Watch project file system changes and sync them to remote pi

remote_host="pi@raspberrycam"
remote_dir="/home/pi/pydev/camguard"

printf "Running initial sync to '%s:%s'\n" "$remote_host" "$remote_dir"
rsync -avP --rsh=ssh "." "$remote_host":"$remote_dir" --exclude="venv" --exclude=".idea/" --exclude="*.log" --exclude="*.python-version" --exclude="**/__pycache__"

printf "Watching file changes in current directory and syncing them to remote shell with args: '%s'\n" "$*"

inotifywait -rm -e create,close_write,move,delete --format %T##%e##%w%f%0 --timefmt "%d-%m-%Y-%H:%M:%S" --exclude "(\.idea)|(.*~)|(venv)|(\.python-version)|(__pycache__)" . |\
    while IFS= read -r event
    do
        echo "***********************"
        echo "$event"
        echo "***********************"

        filepath=$(awk -F## '{print $3}' <<< "$event")
        echo "filepath: ${filepath}"

        remotepath="$remote_dir/$filepath"
        echo "remotepath: ${remotepath}"

        rsync -avP --rsh=ssh "$filepath" "$remote_host":"$remotepath"
    done
