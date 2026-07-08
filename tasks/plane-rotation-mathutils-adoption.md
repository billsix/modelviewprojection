# Adopt gacalc's plane_rotation in the mathutils rotation facades

**Status:** proposed — UNBLOCKED 2026-07-09 (gacalc 0.0.8 is on PyPI and
ctc already runs on it); ready to implement on Bill's go-ahead.
**Created:** 2026-07-09 (relocated from geometricalgebra
`tasks/archive/2026/07/09/plane-rotation-pretag-and-mvp-adoption.md`,
which has the full review findings, the measured sympy-leak numbers,
and the per-theta cost model).

## Why

The facades (`rotate`, `rotate_90_degrees`, `rotate_x/y/z`) each
hand-build `to_vector = cos θ·a + sin θ·b` and call `rotor_rotation`
— re-deriving the plane on every call. Worse, nothing calls
`interpolate` directly: `cayleyscene.py` calls `edge.fn.at(t)` per edge
**per animation frame**, and `.at(t)` re-runs the whole facade (fresh
trig, fresh `rotor_from_vectors`, fresh `normalize`) every frame.
`plane_rotation` derives the plane ONCE at factory time; per θ is two
trig calls + one small rotor; per application is one closed-form
sandwich.

## Plan

- `mathutils`: module-level factories —
  `_xy = plane_rotation(Vector2.e_1, Vector2.e_2)`,
  `rotate(θ) = _xy(θ)`, `rotate_90_degrees() = _xy(π/2)`;
  3D: `rotate_x` on `plane_rotation(Vector3.e_2, Vector3.e_3)`,
  `rotate_y` on `(e_3, e_1)`, `rotate_z` on `(e_1, e_2)`;
  keep the facades' `R_{<θ>}` / `RX/RY/RZ_{<θ>}` labels via the
  factory's `latex_repr`/`latex_repr_inv` hooks;
  `rotate_around` unchanged (it composes `rotate`).
- mvpvisualization / cayleyscene / demos: **no code changes** — they
  consume `.at(t)`, which plane_rotation's closure serves from the
  cached plane (this is where the per-frame win lands).
- Book: the `doc-region` blocks around the facades feed chapters —
  prose update to teach plane+angle folds into gacalc-math-migration
  Phase 4 (flag there; don't block this task).
- ctc: kinetix needs nothing (already on the factory; 0.0.8's numeric
  guard repairs its float-ness).

## Gates

format.sh (ruff + ty over src), mvp pytest (mathutils/transforms tests),
a demo spot-run by Bill (any rotating demo + one Cayley animation), and
a before/after timing of `fn.at(t)` in a cayleyscene-style loop.
