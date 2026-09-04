#!/usr/bin/env bash
# Re-verify the step-1 inline of ALL 10 games (frame-identity trace), robust to
# the environment's flaky Xvfb: a fresh X server is started before EACH game, so
# the cumulative wedge that hung earlier runs (window creation blocking on a
# degraded X) cannot build up. Each game's capture is SIGKILL-bounded by
# verify_step1.sh, so nothing can hang the run. Results (one line per game, then
# ALL-DONE) go to stdout.
#
# Usage:  bash tasks/adhoc/pgzero-gl-inline/run_all_step1.sh
set -u
cd "$(git rev-parse --show-toplevel)"

GAMES="vol1/boing/boing vol1/cavern/cavern vol1/myriapod/myriapod \
vol1/bunner/bunner vol1/soccer/soccer vol2/kinetix/kinetix vol2/avenger/avenger \
vol2/eggzy/eggzy vol2/leadingedge/leadingedge vol2/beatstreets/beatstreets"

fresh_xvfb() {
  pkill -9 -x Xvfb 2>/dev/null
  rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 2>/dev/null
  nohup Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &
  # busy-wait (no sleep) up to ~a few seconds for the socket to appear
  for _ in $(seq 1 2000); do [ -e /tmp/.X11-unix/X99 ] && return 0; done
  return 0
}

for g in $GAMES; do
  fresh_xvfb
  tasks/adhoc/pgzero-gl-inline/verify_step1.sh "ports/codetheclassics/$g.py" 2>/dev/null
done
echo "ALL-DONE"
