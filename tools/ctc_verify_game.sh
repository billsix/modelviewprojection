#!/usr/bin/env bash
# Behaviour-preservation gate for the Code-the-Classics games: prove that the
# WORKING-TREE copy of a game draws frame N byte-identically to a committed
# baseline of the same game. Run it after ANY edit to a game file (the games
# are behaviour-faithful ports: same pixels, or say why not), together with
# tools/ctc_state_trace.py, which covers the input paths this cannot. Promoted
# from tasks/adhoc/codetheclassics-tighten-games/ on 2026-09-05, where it
# gated all ten games' tightening (tasks/archive/2026/09/05/codetheclassics-tighten-games.md).
#
# The baseline is `git show <ref>:<game>` (default ref: HEAD), written beside
# the game as _baseline_<name>.py so it finds the same images/ sounds/ music/
# folders (the games resolve assets from their own file's directory). Each
# capture is a seeded, frame-counted PNG from capture_frame.py (the step-1
# harness): the baseline is captured TWICE (a determinism check, so a game
# that isn't reproducible even unchanged can't masquerade as a pass), then the
# working-tree file once, and the PNGs are compared with ImageMagick's AE
# (absolute-error pixel count) metric. AE=0 on both comparisons is a pass.
#
# Runs the captures in the project's own container (the nested mvp image),
# under the sandbox's Xvfb on :99. Reuses tasks/adhoc/pgzero-gl-inline/
# capture_frame.py unchanged (that adhoc dir lives until its umbrella,
# tasks/pgzero-gl-inline-strip-reextract.md, archives -- move capture_frame.py
# into tools/ first when it does).
#
# Usage (repo root as CWD, `Xvfb :99` running, `make image` built):
#   tools/ctc_verify_game.sh \
#       ports/codetheclassics/vol1/boing/boing.py [frame=180] [ref=HEAD]
# Compare two DIFFERENT working-tree files (e.g. boing.py vs boing_gl1.py):
#   ... verify_game.sh <a.py> [frame] --against <b.py>
set -u
game="$1"; N="${2:-180}"
dir=$(dirname "$game"); base=$(basename "$game" .py)
capture=tasks/adhoc/pgzero-gl-inline/capture_frame.py
out=${VERIFY_OUT:-/tmp/claude-verify}; mkdir -p "$out"

if [ "${3:-}" = "--against" ]; then
  # A/B mode: the "baseline" is another working-tree file in the same dir.
  other=$(basename "$4" .py)
  [ "$(dirname "$4")" = "$dir" ] || { echo "$base: --against file must be in $dir"; exit 1; }
  baseline="$other"; cleanup=""
else
  ref="${3:-HEAD}"
  baseline="_baseline_$base"
  git show "$ref:$game" > "$dir/$baseline.py" || { echo "$base: no $ref version"; exit 1; }
  cleanup="$dir/$baseline.py"
fi

# SIGKILL-bounded: podman ignores SIGTERM, and a wedged Xvfb can hang window
# creation forever otherwise.
timeout -s KILL 240 podman run --cgroups=disabled --rm \
  -e DISPLAY=:99 -e PGZERO_MAX_FRAMES="$N" -e CAPTURE_FRAME="$N" \
  -v /tmp/.X11-unix:/tmp/.X11-unix -v "$(pwd)":/mvp:z -v "$out":/hostout:z \
  --entrypoint /bin/bash localhost/modelviewprojection:latest -c "
    source /venv/bin/activate && cd /mvp/$dir
    for pair in $baseline.py:b1 $baseline.py:b2 $base.py:cur; do
      f=\${pair%:*}; o=\${pair#*:}
      rm -f /hostout/${base}_\$o.png
      CAPTURE_OUT=/hostout/${base}_\$o.png \
        python /mvp/$capture \$f >/hostout/${base}_\$o.log 2>&1
    done
  " >"$out/run_$base.log" 2>&1
[ -n "$cleanup" ] && rm -f "$cleanup"

b1=$out/${base}_b1.png; b2=$out/${base}_b2.png; cur=$out/${base}_cur.png
for f in "$b1" "$b2" "$cur"; do
  [ -f "$f" ] || { echo "$base: CAPTURE-FAIL (missing $(basename "$f"); see $out/${base}_*.log)"; exit 1; }
done
# `magick compare -metric AE` prints e.g. "0 (0)"; keep the leading count.
det=$(magick compare -metric AE "$b1" "$b2" null: 2>&1 | awk '{print $1}')
idt=$(magick compare -metric AE "$b1" "$cur" null: 2>&1 | awk '{print $1}')
if [ "$det" != "0" ]; then echo "$base: NONDETERMINISTIC (baseline-vs-baseline AE=$det; identity AE=$idt)"; exit 2; fi
[ "$idt" = "0" ] && echo "$base: PASS (frame $N byte-identical to $baseline, AE=0)" \
                 || { echo "$base: FAIL (AE=$idt vs $baseline)"; exit 1; }
