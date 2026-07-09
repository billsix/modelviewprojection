# Adopt gacalc's plane_rotation in the mathutils rotation facades

**Status:** DONE 2026-07-09 — implemented, Bill's display spot-run good
("spot-run is good"), plus his follow-up round (direct typed bindings,
rotate_90_degrees retired, wedge predicates moved to the rasterizer,
book TODOs, format.sh coverage). Archived.

## What landed

- `mathutils`: four module-level factories, planes derived once at
  import — `_xy_rotation` (`Vector2.e_1→e_2`, labels `R_{<θ>}`), and
  for 3D `_yz_rotation` (RX), `_zx_rotation` (RY), `_xy3_rotation`
  (RZ). `rotate`/`rotate_x/y/z` are now one-line lookups;
  `rotate_90_degrees` reuses `rotate` + `dataclasses.replace` for its
  traditional `R_{<xy90>}` label; `rotate_around` untouched
  (composition). `rotor_rotation` no longer imported. The doc-region
  markers stay in place around the new bodies (book prose update is
  Phase 4 of gacalc-math-migration, as planned).
- **Measured (container)**: cayleyscene-style `fn.at(t)` + apply:
  **160.6 µs → 6.4 µs (25×)** vs the old facade shape, and results are
  plain `float` instead of sympy `Float` — the leak that made every
  downstream demo op ~6× slower is gone for mvp.
- Contract suite: values identical to the old trig for all four facades
  across angles; labels preserved (incl. `R_{<xy90>}` and negative-angle
  inverses); `at(0/0.5/1)`, `inverse`, and `compose` behave (angles add);
  numeric results are `float`. mvp pytest 60 passed; format.sh fully
  green (7/7 steps incl. `ty check src`).
- mvpvisualization / cayleyscene / demos: zero changes, by design.

## Bill's follow-up round (2026-07-09, same session)

- **Facades are direct typed bindings** — no wrapper defs, no private
  globals: `rotate: typing.Callable[[float], InvertibleFunction[Vector2]]
  = plane_rotation(...)` (and rotate_x/y/z for Vector3). Module scope is
  deliberate and commented: the plane derives once; rebinding per call
  would re-derive it.
- **`rotate_90_degrees` retired** (no external callers; quarter turn =
  `rotate(math.radians(90))`; test updated accordingly).
- **Orientation predicates moved to their sole consumer**:
  `is_counter_clockwise`/`is_clockwise`/`is_parallel` now live in
  `framebuffer/softwarerendering.py` next to the point-in-triangle test,
  and compute the **wedge** (Bill chose it over rotate-90-then-dot):
  `(v1 ^ v2).coefficient(Bivector2.e_12)` — exact classic arithmetic,
  closed-form fast (3 calls/pixel in the rasterizer), GA-native.
  NB gacalc wart found: graded `__xor__` is annotated `-> Self` though
  the wedge widens to Bivector2 — `coefficient()` is the typed read-back
  (a candidate note for gacalc's board).
- **Book**: ch07/ch14 got TODO blocks above the affected includes;
  `tasks/book-rotate-prose-update.md` carries the rewrite (Bill will do
  the prose).
- **format.sh now covers `assignments/`** (ruff check+format) — and with
  this round's lint-policy work (S311/T201 per-file-ignores with
  rationale for demos/assignments/plotsforbook/notebooksrc, eight B008
  identity-default hoists in nbplotutils, one E501 wrap), **every step
  of the gate is green across assignments+src+tests+ports for the first
  time** — ruff, format --check, and all five ty targets. 60 pytest.
- New task from Bill: `tasks/assignments-review.md` (modernize the
  exercises relative to the demos); CLAUDE.md/README now describe
  `assignments/`.
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
