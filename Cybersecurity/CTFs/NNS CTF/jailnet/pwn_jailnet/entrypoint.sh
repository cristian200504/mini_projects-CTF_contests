#!/bin/sh
set -eu

printf '%s\n' "$FLAG" > /flag.txt
unset FLAG

exec janet /app/server.janet