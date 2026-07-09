#!/bin/env bash

export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate

# Fail-on-any-step (2026-07-09): every step runs (so one pass reports ALL
# the red, not just the first), and the script exits nonzero if ANY step
# failed.  Before this, the exit code was the LAST command's alone, so the
# gate could report green off the final ty check while earlier steps were
# red -- which is exactly how 79 src diagnostics hid for weeks (see
# tasks/archive/2026/07/09/src-ty-diagnostics-after-ty-bump.md).
status=0
run() { "$@" || status=1; }

run ruff check assignments --fix
run ruff check src --fix
run ruff check tests --fix
# The ports (Code the Classics shim + games, OpenGL SuperBible) are formatted
# too, as of 2026-07-08 -- the old byte-faithful "no ruff on the games" rule
# was retired along with the structural modernization (see the ctc-* task
# series); the games stay BEHAVIOUR-faithful only.
run ruff check ports --fix
run ruff format assignments --line-length=80
run ruff format src --line-length=80
run ruff format tests --line-length=80
run ruff format ports --line-length=80
run ty check /mvp/src
run ty check /mvp/tests
# Code-the-Classics pygame compatibility shim + the typed game ports.
run ty check /mvp/ports/codetheclassics/pgzero_gl
run ty check /mvp/ports/codetheclassics/vol1
run ty check /mvp/ports/codetheclassics/vol2

exit $status
