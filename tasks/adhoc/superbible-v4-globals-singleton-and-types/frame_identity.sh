#!/usr/bin/env bash
# Copyright (c) 2026 William Emerison Six
#
# Frame-identity gate for the SuperBible v4 AppState refactor: for each given
# port script, capture frames headlessly from the tree at a git ref (the
# pre-refactor baseline) twice, and from the working tree once, and compare.
#   SAME     -- working tree matches the baseline, and the baseline is
#               deterministic (its two runs agree)
#   DIFF     -- working tree differs from a deterministic baseline: a real
#               behaviour change
#   NONDET   -- the baseline's two runs disagree, so identity can't be judged
#               from pixels; the line says whether cur matched either run
#   ERROR    -- a capture failed (see the log under the output dir)
#
# Requires the project image (make image) and an Xvfb on :99 in the sandbox:
#   Xvfb :99 -screen 0 1280x800x24 &
#
# Usage (repo root):
#   tasks/adhoc/superbible-v4-globals-singleton-and-types/frame_identity.sh \
#       <ref> <outdir> <script> [<script> ...]
# Scripts are repo-relative paths under ports/openglsuperbiblev4/.
set -uo pipefail

REF="${1:?usage: frame_identity.sh <ref> <outdir> <script>...}"
OUT="${2:?usage: frame_identity.sh <ref> <outdir> <script>...}"
shift 2
REPO="$(git rev-parse --show-toplevel)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${CONTAINER_NAME:-localhost/modelviewprojection}"
FRAMES="${FRAMES:-3 12}"

mkdir -p "${OUT}/base-tree"
OUT="$(cd "${OUT}" && pwd)"
rm -rf "${OUT}/base-tree"
mkdir -p "${OUT}/base-tree"
git -C "${REPO}" archive "${REF}" ports/openglsuperbiblev4 \
    | tar -x -C "${OUT}/base-tree"

podman run --rm --cgroups=disabled \
    -e DISPLAY=:99 -e MVP_GLFW_X11=1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v "${REPO}":/mvp:Z \
    -v "${OUT}":/out:Z \
    -v "${HERE}/capture_frames.py":/tmp/capture_frames.py:Z \
    --entrypoint /bin/bash "${IMAGE}" -c '
source /venv/bin/activate
unset WAYLAND_DISPLAY
FRAMES="$1"; shift
status=0
mkdir -p /tmp/run && cd /tmp/run
for script in "$@"; do
    tag="$(echo "$script" | tr / _)"
    ok=1
    for which in base base2 cur; do
        case "$which" in
            cur) root=/mvp ;;
            *) root=/out/base-tree ;;
        esac
        dir="/out/$tag/$which"
        rm -rf "$dir"; mkdir -p "$dir"
        if ! timeout -s KILL 120 python /tmp/capture_frames.py \
                "$root/$script" "$dir" $FRAMES > "$dir/log" 2>&1; then
            ok=0
        fi
    done
    if [ "$ok" = 0 ]; then
        echo "ERROR  $script"; status=1; continue
    fi
    verdict="$(python - "/out/$tag" $FRAMES <<PY
import pathlib, sys
from PIL import Image, ImageChops
root: pathlib.Path = pathlib.Path(sys.argv[1])
frames: list[str] = sys.argv[2:]
def same(a: str, b: str) -> bool:
    for frame in frames:
        pa: pathlib.Path = root / a / f"frame{frame}.png"
        pb: pathlib.Path = root / b / f"frame{frame}.png"
        if not pa.exists() or not pb.exists():
            return False
        diff = ImageChops.difference(Image.open(pa), Image.open(pb))
        if diff.getbbox() is not None:
            return False
    return True
if same("base", "base2"):
    print("SAME" if same("base", "cur") else "DIFF")
else:
    matched: bool = same("base", "cur") or same("base2", "cur")
    print("NONDET (cur matches a base run)" if matched else "NONDET (cur matches neither)")
PY
)"
    echo "$verdict  $script"
    case "$verdict" in SAME*|"NONDET (cur matches a base run)") ;; *) status=1 ;; esac
done
exit $status
' _ "${FRAMES}" "$@"
