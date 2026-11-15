#!/usr/bin/env bash
# Copyright (c) 2026 William Emerison Six
#
# Run both Code-the-Classics behaviour gates on every game (or the games named
# as arguments, e.g. `boing bunner`) against a git ref (REF=..., default
# master). Use it after a change that touches every game at once, such as an
# edit to the shared engine modules in src/modelviewprojection/pgzero_gl/:
#   1. tools/ctc_verify_game.sh -- frame-180 pixel identity (attract mode);
#   2. tools/ctc_state_trace.py on the ref's copy and the working tree, with
#      one scripted key sequence, compared by tools/ctc_compare_traces.py.
# Prints one PASS/FAIL line per gate per game and exits non-zero if any failed.
# Needs `Xvfb :99` and the nested localhost/modelviewprojection image. Run from
# anywhere; the repo root is derived from this script's path. A capture that
# times out on the UNCHANGED baseline is a flake (seen once, avenger,
# 2026-11-15): re-run that game alone.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
ref="${REF:-master}"
frames=300
# Start a game, then move, fire and pause: each game reads some of these keys.
keys="5:space:press,6:space:release,40:up:press,80:up:release"
keys+=",90:left:press,130:left:release,140:right:press,180:right:release"
keys+=",190:down:press,220:down:release,230:z:press,240:z:release"
keys+=",250:a:press,260:a:release,265:space:press,266:space:release"
out=${VERIFY_OUT:-/tmp/claude-verify}
mkdir -p "$out"
status=0
names=("$@")
[ "${#names[@]}" -eq 0 ] && names=(boing boing_gl1 bunner cavern myriapod
  soccer avenger beatstreets eggzy kinetix leadingedge)
for name in "${names[@]}"; do
  game=$(ls ports/codetheclassics/vol*/*/"$name".py)
  dir=$(dirname "$game")
  if tools/ctc_verify_game.sh "$game" 180 "$ref" >"$out/verify_$name.txt" 2>&1
  then echo "PASS frame  $name"
  else echo "FAIL frame  $name (see $out/verify_$name.txt)"; status=1
  fi
  skip=""
  [ "$name" = leadingedge ] && skip="track"
  git show "$ref:$game" >"$dir/_baseline_$name.py"
  timeout -s KILL 600 podman run --cgroups=disabled --rm -e DISPLAY=:99 \
    -v /tmp/.X11-unix:/tmp/.X11-unix -v "$(pwd)":/mvp:z -v "$out":/hostout:z \
    --entrypoint /bin/bash localhost/modelviewprojection:latest -c "
      source /venv/bin/activate && cd /mvp
      python tools/ctc_state_trace.py $dir/_baseline_$name.py $frames \
        '$keys' '$skip' >/hostout/trace_${name}_base.txt 2>/hostout/trace_${name}_base.err
      python tools/ctc_state_trace.py $game $frames \
        '$keys' '$skip' >/hostout/trace_${name}_cur.txt 2>/hostout/trace_${name}_cur.err
    " >"$out/trace_run_$name.log" 2>&1
  rm -f "$dir/_baseline_$name.py"
  if [ -s "$out/trace_${name}_base.txt" ] && python3 tools/ctc_compare_traces.py \
       "$out/trace_${name}_base.txt" "$out/trace_${name}_cur.txt" \
       >"$out/compare_$name.txt" 2>&1
  then echo "PASS trace  $name ($(wc -l <"$out/trace_${name}_cur.txt") frames)"
  else echo "FAIL trace  $name (see $out/compare_$name.txt)"; status=1
  fi
done
exit $status
