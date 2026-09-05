# Swap myriapod's local `rotate_90_degrees` for gacalc's `quarter_turn` (on the next gacalc release)

**Status:** blocked — waiting on gacalc to ship a g2 quarter-turn and a release that includes it
**Priority:** 8
**Difficulty:** 2
**Blocked on:** gacalc implementing the g2 `quarter_turn` / `rotate_90_degrees` (its task
`tasks/add-quarter-turn-to-g2.md`, github.com/billsix/geometricalgebra — still a *proposed* design
question as of 2026-09-05) AND cutting a release that contains it.
**Recheck:** `pip index versions gacalc` (or the PyPI JSON API) shows a release **> 0.0.18** whose
`gacalc.g2` exports a `quarter_turn` / `rotate_90_degrees`; confirm with
`python -c "import gacalc.g2 as g2; print(hasattr(g2, 'quarter_turn'), hasattr(g2, 'rotate_90_degrees'))"`
in a throwaway venv with that version installed. When true, this is unblocked.

## BLUF

`ports/codetheclassics/vol1/myriapod/myriapod.py` defines its **own** local
`rotate_90_degrees: InvertibleFunction[Vector]` (≈ `myriapod.py:1980`) — a 90° turn in the e₁e₂
plane, used to build the 0/90/180/270 `_rotations` table for the sprite's `in_edge` direction. This
is a **deliberate temporary duplication** of a convenience gacalc is expected to grow. Once gacalc
ships the g2 quarter-turn, **delete myriapod's local copy and import gacalc's**, so there is one
source of truth for "multiply a vector by the unit pseudoscalar to turn it a quarter turn."

## Context (cold-start)

- **The duplication is intentional, not an oversight.** The 90° turn in 2-D GA is exactly
  multiplication by the unit pseudoscalar `e_12` (`(x, y) → (-y, x)`) — exact, no `cos`/`sin`.
  gacalc's `tasks/add-quarter-turn-to-g2.md` proposes adding this as a named `InvertibleFunction`
  (`quarter_turn` / `rotate_90_degrees`, **g2-only** — the general planar version was removed from
  gacalc for silently mis-transforming e₃+ vectors). Until that lands and releases, myriapod carries
  its own inline copy so it works on the currently-pinned `gacalc==0.0.18`.
- **Current state:** myriapod's local `rotate_90_degrees` is a plain
  `InvertibleFunction(func=…, inverse=…, latex_repr=…)` built from released gacalc primitives — it
  works and is play-tested. `inverse(rotate_90_degrees)` gives the −90° turn; the `_rotations` table
  indexes 0/90/180/270 by `in_edge`.
- **Related:** the gacalc feature task `tasks/add-quarter-turn-to-g2.md`
  (github.com/billsix/geometricalgebra); the pin is bumped in mvp per
  `CLAUDE.md` › "Keeping the Dockerfile, Makefile, and dependencies in sync" (bump BOTH
  `requirements.txt`'s `gacalc==` and the Dockerfile's `ARG GACALC_VERSION`).

## The work (once unblocked)

1. Bump the gacalc pin to the release that has the quarter-turn (both `requirements.txt` and the
   Dockerfile `ARG GACALC_VERSION`), rebuild the image.
2. Delete myriapod's local `rotate_90_degrees` definition; `from gacalc.g2 import quarter_turn`
   (or whatever gacalc named it — check the released module) and use it in the `_rotations` table.
3. Keep `inverse(...)` for the −90° arm exactly as now (gacalc's version is an `InvertibleFunction`,
   so `inverse(quarter_turn)` works identically).
4. **Verify behavior-identical** — the sprite-direction turns must be pixel-for-pixel unchanged. Run
   the seeded frame-capture check (`tasks/adhoc/pgzero-gl-inline/capture_frame.py`) on myriapod
   before/after: frame-180 byte-identical. Then `make test` + `make format` green.

## Done-state

myriapod imports the quarter-turn from `gacalc.g2` (no local copy), behavior byte-identical, gates
green, pin bumped.
