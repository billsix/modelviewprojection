#!/bin/env bash

export VIRTUAL_ENV_DISABLE_PROMPT=1
# Activate the container's venv when it exists; outside the container (running
# format.sh from the repo root on the host) it's absent -- use the caller's env.
# Every path below is RELATIVE to the repo root, so format.sh runs identically
# in the container (cd /mvp) and on the host (cd <repo>) -- see the .extrabashrc
# exit hook, which cd's to the project root before calling it.
[ -f /venv/bin/activate ] && source /venv/bin/activate

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
run ruff format assignments
run ruff format src
run ruff format tests
run ruff format ports
run ty check src
run ty check tests
# The Code-the-Classics pygame compatibility shim now lives IN the package
# (src/modelviewprojection/pgzero_gl), so `ty check src` above covers it;
# these are the typed game ports that import it.
run ty check ports/codetheclassics/vol1
run ty check ports/codetheclassics/vol2

exit $status
