#!/usr/bin/env bash
# List every distinct tasks/<...>.md path cited in tracked text that does not
# resolve, one per line, sorted. Run from anywhere inside the repo.
#
# Usage: tasks/adhoc/repoint-dangling-task-doc-paths/discover.sh [> data/dangling.txt]

cd "$(git rev-parse --show-toplevel)" || exit 1
# The task doc and this directory quote dangling paths on purpose.
git grep -ohE "tasks/[A-Za-z0-9_./-]+\.md" -- . \
    ":!tasks/repoint-dangling-task-doc-paths.md" \
    ":!tasks/adhoc/repoint-dangling-task-doc-paths" |
    sort -u | while read -r path; do
    [ -e "$path" ] || printf '%s\n' "$path"
done
