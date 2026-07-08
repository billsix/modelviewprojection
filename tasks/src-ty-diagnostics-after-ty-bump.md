# Fix the 79 `ty check src` diagnostics exposed by the Fedora ty bump

**Status:** diagnostics RESOLVED 2026-07-09 — `ty check src` is **0**
(was 79; all of them died with the crossproduct-demo removal, see
archive/2026/07/09/remove-crossproduct-demo.md). src, tests, and the whole
ctc tree are now ty-clean. The ONLY remaining item is this task's
follow-through decision: flip `entrypoint/format.sh` to fail-on-any-step
(set -e or per-step exit-code collection) so the gate can never again
report green off the last step alone — needs Bill's go-ahead.
**Created:** 2026-07-08

## Context

The Fedora 44 `ty` package (reinstalled fresh at every `make image`) moved to
a stricter version, which on 2026-07-08 turned two previously-green
`format.sh` steps red. The Code-the-Classics half (vol2's ~120 `game`-union
errors) was fixed the same day (see the resolution in
tasks/ctc-more-types.md); **this task is the mvp-`src/` half**: `ty check
/mvp/src` now reports **79 diagnostics**, though `make format` still exits 0
because the vol2 check happens to run last in `entrypoint/format.sh` — the
red step is visible in the output but doesn't fail the script. (Consider
also making format.sh fail if ANY step fails, once the steps are clean —
today's exit-code-of-last-command behavior is what masked this.)

## Where they are (from the 2026-07-08 in-container run)

| file | count | shape |
|---|---|---|
| `mathdemos/crossproduct.py` | 76 | `Object of type 'object' has no attribute x/y/z/rot_x/rot_y/...` |
| `util/nbplotutils.py` | 8 | (inspect) |
| `plotsforbook/plotutils/matplotgraphs.py` | 2 | (inspect) |
| `notebooksrc/ndc.py` | 2 | (inspect) |
| `notebooksrc/crossproduct.py` | 1 | (inspect) |

The dominant pattern (mathdemos/crossproduct.py, e.g. lines ~646-659): the
demo's `g`-style state holds vectors/camera in fields typed `object` (or
inferred as `object`), and the newer ty rejects attribute access on
`object` where the old one didn't. Likely fixes: give those fields their
real types (`Vector3`-ish records, the camera dataclass) — the same
declare-the-fields treatment the CTC dataclasses pass applied to the games;
mathdemos may even want the identical `@dataclass(eq=False)` pattern.

## Gate

In-container `format.sh` with **every** step green (src, tests, pgzero_gl,
vol1, vol2) — and then flip format.sh to fail-on-any-step so this can't
regress silently again.
