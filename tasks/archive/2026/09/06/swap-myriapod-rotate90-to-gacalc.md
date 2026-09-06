# Swap myriapod's local `rotate_90_degrees` for gacalc's `g2.rotate_90_degrees` (on the next gacalc release)

**Status:** DONE — 2026-09-06. myriapod now imports gacalc's g2.rotate_90_degrees() factory; frame gate AE=0. gacalc pinned 0.0.20 (requirements.txt + Dockerfile). ty + ruff + 104 pytest green. Archived same day. — gacalc HAS the feature (implemented 2026-09-06 in its working tree as
`g2.rotate_90_degrees()` + `g2.Vector.rotate_90_degrees()`, record
`tasks/archive/2026/09/06/add-quarter-turn-to-g2.md` in github.com/billsix/geometricalgebra).
Unblocked by the maintainer 2026-09-06; step 1 below is the gacalc release itself (PyPI was at
0.0.19 when this was written — 0.0.20, a PATCH bump, is the one to pin).
**Priority:** 4
**Difficulty:** 2

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
  gacalc now has exactly this (2026-09-06): the module-level `g2.rotate_90_degrees()` factory
  returning an `InvertibleFunction[Vector]` plus the `g2.Vector.rotate_90_degrees()` method, both the
  generated closed form of `v * e_12`, **g2-only** (the general planar version was removed from gacalc
  for silently mis-transforming e₃+ vectors), guarding with `TypeError` on non-`g2.Vector` input.
  Until it *releases*, myriapod carries its own inline copy so it works on the pinned
  `gacalc==0.0.19`.
- **Current state:** myriapod's local `rotate_90_degrees` is a plain
  `InvertibleFunction(func=…, inverse=…, latex_repr=…)` built from released gacalc primitives — it
  works and is play-tested. `inverse(rotate_90_degrees)` gives the −90° turn; the `_rotations` table
  indexes 0/90/180/270 by `in_edge`.
- **Related:** the gacalc feature task `tasks/add-quarter-turn-to-g2.md`
  (github.com/billsix/geometricalgebra); the pin is bumped in mvp per
  `CLAUDE.md` › "Keeping the Dockerfile, Makefile, and dependencies in sync" (bump BOTH
  `requirements.txt`'s `gacalc==` and the Dockerfile's `ARG GACALC_VERSION`).

## The work (once unblocked)

1. Release gacalc with the quarter turn (maintainer: promote `[Unreleased]`, bump, tag, publish),
   then bump the gacalc pin to that release (both `requirements.txt` and the Dockerfile
   `ARG GACALC_VERSION`) and rebuild the image.
2. Delete myriapod's local `rotate_90_degrees` definition; `from gacalc.g2 import rotate_90_degrees`
   and use `rotate_90_degrees()` (it is a *factory* — call it once to get the `InvertibleFunction`)
   in the `_rotations` table.
3. Keep `inverse(...)` for the −90° arm exactly as now (gacalc's version is an `InvertibleFunction`,
   so `inverse(rotate_90_degrees())` works identically; its guard raises `TypeError` on a non-vector,
   which the table never feeds it).
4. **Verify behavior-identical** — the sprite-direction turns must be pixel-for-pixel unchanged. Run
   the seeded frame-capture check (`tools/ctc_verify_game.sh`) on myriapod
   before/after: frame-180 byte-identical. Then `make test` + `make format` green.

## Done-state

myriapod imports the quarter-turn from `gacalc.g2` (no local copy), behavior byte-identical, gates
green, pin bumped.
