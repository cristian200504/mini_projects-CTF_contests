#!/bin/sh
set -eu

/usr/local/bin/go-sanitizer &

exec gunicorn \
  --bind 0.0.0.0:${PORT:-5050} \
  --workers 2 \
  --threads 4 \
  --timeout 60 \
  app:app
