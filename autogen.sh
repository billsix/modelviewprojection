#!/bin/sh
set -e

echo "Running autoreconf..."
autoreconf --install --force

echo
echo "Now run ./configure && make"

