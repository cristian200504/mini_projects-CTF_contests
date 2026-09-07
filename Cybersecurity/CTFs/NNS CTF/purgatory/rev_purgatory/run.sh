#!/bin/sh
set -eu

exec erl -noshell -pa /app \
    -run purgatory_runner main \
    /app/releases/old.beam \
    /app/releases/new.beam
