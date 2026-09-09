#!/bin/bash
# Copyright (c) 2026 William Emerison Six
#
# Run a GL script (a demo or an assignment) headlessly in the project image and
# prove it renders -- see render_probe.py for what is actually measured.
#
#   tasks/adhoc/assignments-review/verify.sh <script> [frames] [png] [hold-keys]
#
#   ./verify.sh assignments/assignment3-strafe.py
#   ./verify.sh assignments/assignment3-strafe.py 10 /tmp/a3.png RIGHT,LEFT_SHIFT
#
# Run from the repo root.  Needs `make image` once (BUILD_DOCS=0 is enough --
# nothing here touches the book) and, in the sandbox, an Xvfb the container can
# share:
#
#   Xvfb :99 -screen 0 1280x800x24 &
#
# The X server stays OUTSIDE the container and its socket is bind-mounted in, so
# the project's own Dockerfile never needs xvfb added to it.
set -euo pipefail

SCRIPT="${1:?usage: verify.sh <script.py> [frames] [png] [hold-keys]}"
FRAMES="${2:-10}"
PNG="${3:-}"
HOLD="${4:-}"

REPO="$(git rev-parse --show-toplevel)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# NOT $DISPLAY: in the sandbox that is :0, the host passthrough, which the
# container cannot reach (X11 auth).  Override with PROBE_DISPLAY if needed.
DISPLAY_NUM="${PROBE_DISPLAY:-:99}"
IMAGE="${CONTAINER_NAME:-localhost/modelviewprojection}"

# --cgroups=disabled is harmless belt-and-braces for nested podman (the repo's
# own Makefile applies it the same way via PODMAN_RUN_FLAGS).
run_args=(--rm --cgroups=disabled
          -e "DISPLAY=${DISPLAY_NUM}"
          -v /tmp/.X11-unix:/tmp/.X11-unix
          -v "${REPO}":/mvp:Z)

probe_args=("/mvp/${SCRIPT}" "${FRAMES}")
if [ -n "${PNG}" ]; then
    # the PNG is written from inside the container, so its directory is mounted
    mkdir -p "$(dirname "${PNG}")"
    run_args+=(-v "$(cd "$(dirname "${PNG}")" && pwd)":/out:Z)
    probe_args+=(--png "/out/$(basename "${PNG}")")
fi
[ -n "${HOLD}" ] && probe_args+=(--hold "${HOLD}")

# PYTHONPATH rather than an editable install: this is a read-only check, and it
# keeps the run from writing an egg-link into the bind-mounted tree.
podman run "${run_args[@]}" \
    -v "${HERE}/render_probe.py":/tmp/render_probe.py:Z \
    --entrypoint /bin/bash "${IMAGE}" -c \
    "source /venv/bin/activate && cd /mvp && PYTHONPATH=/mvp/src \
     python /tmp/render_probe.py ${probe_args[*]}"
