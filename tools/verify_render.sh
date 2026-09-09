#!/usr/bin/env bash
# Copyright (c) 2026 William Emerison Six
#
# Render gate for a GL script in this repo -- a demo, a visualization, or an
# assignment: prove it still draws something, headlessly. Run it after editing
# one of those files. Promoted from tasks/adhoc/assignments-review/ on
# 2026-09-09, where it gated the assignment re-syncs
# (tasks/archive/2026/09/09/assignments-1-and-2-review.md).
#
# Sibling of tools/ctc_verify_game.sh, and deliberately NOT the same check:
# that one proves a Code-the-Classics game is pixel-identical to a committed
# baseline (AE=0), because those are behaviour-faithful ports. This one proves
# a demo or assignment rendered AT ALL, and reports the colour histogram, since
# the demos have no byte-identical contract to hold them to -- a colour count
# per object is what you compare by eye between two runs.
#
# What it measures and why it reads the framebuffer instead of screenshotting:
# see the header of tools/render_probe.py, which does the work.
#
# Requires, once:
#   make image            # BUILD_DOCS=0 is enough; nothing here touches the book
#   Xvfb :99 -screen 0 1280x800x24 &
# The X server stays OUTSIDE the container and its socket is bind-mounted in,
# so the project's Dockerfile never needs xvfb added to it.
#
# Usage (from the repo root):
#   tools/verify_render.sh <script> [frames] [png] [hold-keys] [--allow-blank]
#
#   tools/verify_render.sh src/modelviewprojection/demos/demo18.py
#   tools/verify_render.sh assignments/assignment3-strafe.py 10 /tmp/a3.png RIGHT,LEFT_SHIFT
#   tools/verify_render.sh assignments/assignment2-screenspace.py 6 "" "" --allow-blank
#
# hold-keys are glfw key names without KEY_ (RIGHT, LEFT_SHIFT, UP), for
# exercising a camera path with nobody at the keyboard. --allow-blank accepts a
# single-colour frame, which is CORRECT for an assignment whose exercise hole is
# what makes the scene appear.
set -euo pipefail

SCRIPT="${1:?usage: verify_render.sh <script.py> [frames] [png] [hold-keys] [--allow-blank]}"
FRAMES="${2:-10}"
PNG="${3:-}"
HOLD="${4:-}"
ALLOW_BLANK="${5:-}"

REPO="$(git rev-parse --show-toplevel)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${CONTAINER_NAME:-localhost/modelviewprojection}"
# NOT $DISPLAY: in the sandbox that is :0, the host passthrough, which the
# container cannot authenticate to. Override with PROBE_DISPLAY if needed.
DISPLAY_NUM="${PROBE_DISPLAY:-:99}"

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
[ -n "${ALLOW_BLANK}" ] && probe_args+=("${ALLOW_BLANK}")

# PYTHONPATH rather than an editable install: this is a read-only check, and it
# keeps the run from writing an egg-link into the bind-mounted tree.
podman run "${run_args[@]}" \
    -v "${HERE}/render_probe.py":/tmp/render_probe.py:Z \
    --entrypoint /bin/bash "${IMAGE}" -c \
    "source /venv/bin/activate && cd /mvp && PYTHONPATH=/mvp/src \
     python /tmp/render_probe.py ${probe_args[*]}"
