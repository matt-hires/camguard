#!/bin/bash
# Author: matt-hires
# Date: 12.12.20 14:01
# Description: Watch project file system changes and sync them to remote pi

remote_host="pi@raspberrycam"
remote_dir="/home/pi/pydev/camguard"
rsync_excludes=("--exclude=venv/" "--exclude=*.log" "--exclude=**/__pycache__" \
"--exclude=.tox/" "--exclude=.git/" "--exclude=.python-version" \
"--exclude=pip-wheel-metadata/" "--exclude=src/*.egg-info/" "--exclude=.vscode/" \
"--exclude=credentials.json")

inotify_excludes='(\.idea)|(.*~)|(venv)|(\.python-version)|(__pycache__)|(\.git)|(\.vscode)'

printf "Running initial sync to '%s:%s'\n" "$remote_host" "$remote_dir"
rsync -avP --force --delete --rsh=ssh '.' "$remote_host":"$remote_dir" "${rsync_excludes[@]}"
echo "Watching file changes in current directory and syncing them to remote shell..."

inotifywait -rm -e create,close_write,move,delete \
    --format '%T##%e##%w%f%0' --timefmt '%d-%m-%Y-%H:%M:%S' \
    --exclude "${inotify_excludes}" . |
    while IFS= read -r event; do
        echo "***********************"
        echo "$event"
        echo "***********************"

        event_name=$(awk -v FS='##' '{print $2}' <<<"$event")
        path=$(awk -v FS='##' '{print $3}' <<<"$event")
        echo "event_name: ${event_name}"

        delete_flags=()
        case "${event_name}" in
        DELETE | MOVED_FROM)
            path=$(dirname "${path}")
            delete_flags+=("--delete")
            ;;
        esac

        echo "path: ${path}"

        remotepath="$remote_dir/$path"
        echo "remotepath: ${remotepath}"

        rsync -avP "${delete_flags[@]}" --rsh=ssh "$path" \
            "$remote_host":"$remotepath" "${rsync_excludes[@]}"
    done
