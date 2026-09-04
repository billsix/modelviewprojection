#!/usr/bin/env bash
# Verify the step-1 inline of ONE game (tasks/pgzero-gl-step1-inline-per-game.md).
#
# Host side: run inline_game.py -> <game>_inlined.py, then ruff --fix + format,
# then ruff check (must be clean). Container side: a frame-identity trace via
# capture_frame.py -- the ORIGINAL is captured twice (a determinism sanity check,
# so a game that isn't reproducible even without the change can't masquerade as a
# pass), then the inlined copy is compared byte-for-byte against it. A pass means
# the inline changed no pixel of frame N: behavior-preserving, proven.
#
# Usage (repo root as CWD, Xvfb on :99, image built):
#   tasks/adhoc/pgzero-gl-inline/verify_step1.sh <game-rel-path> [frame]
set -u
game="$1"; N="${2:-180}"
dir=$(dirname "$game"); base=$(basename "$game" .py)
inlined="$dir/${base}_inlined.py"
adhoc=tasks/adhoc/pgzero-gl-inline

python3 "$adhoc/inline_game.py" "$game" "$inlined" >/dev/null || { echo "$base: INLINE-FAIL"; exit 1; }
ruff check --fix "$inlined" >/dev/null 2>&1
ruff format "$inlined" >/dev/null 2>&1
if ! ruff check "$inlined" >/tmp/ruff_$base.txt 2>&1; then
  echo "$base: RUFF-FAIL"; head -8 /tmp/ruff_$base.txt; exit 1
fi

# Hard per-game timeout so a wedged capture can never block the run forever
# (e.g. a wedged Xvfb makes window creation hang). -s KILL because podman ignores
# SIGTERM -- plain `timeout` would send TERM and then wait forever.
timeout -s KILL 150 podman run --cgroups=disabled --rm \
  -e DISPLAY=:99 -e PGZERO_MAX_FRAMES="$N" -e CAPTURE_FRAME="$N" -e PYTHONPATH=/mvp/src \
  -v /tmp/.X11-unix:/tmp/.X11-unix -v "$(pwd)":/mvp:z -v /tmp:/hostout:z \
  --entrypoint /bin/bash localhost/modelviewprojection:latest -c "
    source /venv/bin/activate && cd /mvp/$dir
    for pair in ${base}.py:o1 ${base}.py:o2 ${base}_inlined.py:inl; do
      f=\${pair%:*}; o=\${pair#*:}
      CAPTURE_OUT=/hostout/${base}_\$o.png \
        python /mvp/$adhoc/capture_frame.py \$f >/dev/null 2>&1
    done
  " >/tmp/run_$base.log 2>&1

o1=/tmp/${base}_o1.png; o2=/tmp/${base}_o2.png; inl=/tmp/${base}_inl.png
[ -f "$o1" ] && [ -f "$o2" ] && [ -f "$inl" ] || { echo "$base: CAPTURE-FAIL (missing pngs)"; exit 1; }
# `magick compare -metric AE` prints e.g. "0 (0)"; take the leading count.
det=$(magick compare -metric AE "$o1" "$o2" null: 2>&1 | awk "{print \$1}")
idt=$(magick compare -metric AE "$o1" "$inl" null: 2>&1 | awk "{print \$1}")
if [ "$det" != "0" ]; then echo "$base: NONDETERMINISTIC (orig-vs-orig AE=$det; identity AE=$idt)"; exit 2; fi
[ "$idt" = "0" ] && echo "$base: PASS (frame $N byte-identical, AE=0)" || { echo "$base: FAIL (AE=$idt)"; exit 1; }
