# `mathutils` helpers: which should be re-expressed in gacalc's vocabulary?

**Status:** proposed — needs go-ahead. **Merged 2026-09-08** from
`mathutils-angle-helpers-via-gacalc-measures.md` (audited 2026-08-24) and
`face-normal-vector3d-io.md` (an older investigation, written before the gacalc migration and
carrying its pre-migration vocabulary). Both were P6/D3, both asked the same question about the
same module, both needed one decision, and both touch the same doctests and the same autodoc page —
so they are one review. The originals are archived at `tasks/archive/2026/09/08/`.
**Priority:** 6
**Difficulty:** 3

## BLUF

`src/modelviewprojection/mathutils.py` keeps the graphics-specific math that gacalc deliberately
does not carry. Three of its helpers compute quantities gacalc now has **named** forms for, and one
of them still speaks tuples at a boundary where both sides hold vectors. Decide, per helper,
whether to re-express it in the shared vocabulary — which ties the book's own words to the library —
or keep the hand-written form because it teaches something the named form hides.

This is a **taste review with three small edits behind it**, not a refactor: every rewrite below is
numerically identical to what is there now.

## Why the two tasks merged

Both are "should this `mathutils` helper speak gacalc?", both are gated on the same kind of
judgment (clarity vs. what the teaching comment shows), and — the practical part — all three
helpers are **book-API-documented via autodoc** and **carry doctests**, so any change to any of them
re-runs the same gate and regenerates the same `api.html`. Doing them in one pass is one review and
one verification instead of two.

## The four decisions

### 1. `sine(v1, v2)` — 2D, signed → `signed_area`?

Today: `float((v1 ^ v2).coeff_e_12) / (|v1| |v2|)`. That numerator **is**
`gacalc.measure.signed_area(v1, v2)` — the e₁₂ coefficient of the wedge is the 2D signed
parallelogram area. Verified 2026-08-24 that `signed_area` works on `g2.Vector`, which is what
`sine` is typed to.

Rewrite: `signed_area(v1, v2) / (float(abs(v1)) * float(abs(v2)))`, keeping the zero-length → `NaN`
guard.

**The counter-argument, and it is real:** `sine` carries a teaching comment documenting the classic
"rotate 90° then dot" trick, and in gacalc's own `nbplotutils.sine` the maintainer **kept** the
rotate-90 form for teaching rather than switching to `signed_area`. That choice was forced there
(that helper runs on the dimensionless `Gn`, where `signed_area` cannot apply) — mvp's is typed to
`g2.Vector`, so the choice here is free. *Recommend: switch, and keep the comment* — the named
measure and the trick can both be on the page.

### 2. `abs_sin(v1, v2)` — 3D, unsigned → `area`? or delete?

Today: `float(abs(v1 ^ v2)) / (|v1| |v2|)`; the numerator **is** `gacalc.measure.area(v1, v2)`.

But `abs_sin` has **no production caller** — only `tests/test_mathutils.py::test_abs_sin` and the
autodoc API page reference it. So this is two decisions in one: rewrite-and-keep, or remove.
*Recommend: rewrite via `area` and keep* — it is public, book-documented API, and the 3D unsigned
counterpart to `sine` is worth having named.

### 3. `cosine(v1, v2)` — **keep as-is** (recorded so it is not re-proposed)

`v1.dot(v2).scalar_part() / (|v1| |v2|)`, any dimension, NaN-safe. It parallels gacalc's own
`MultiVectorBase.cosine` method (Hestenes & Sobczyk p. 14) but adds the NaN-on-zero-length
behaviour mvp depends on: `framebuffer/softwarerendering.py`'s parallel test does
`math.isclose(cosine(...), 1.0)`, while the gacalc method **raises** on a zero vector. Do **not**
replace it with the method.

### 4. `_face_normal` — should it take and return `Vector` instead of tuples?

`util/shading.py:33` — `_face_normal(a, b, c) -> tuple[float, float, float]` takes three
`Sequence[float]` and returns a tuple, so it wraps (`Vector(*a)`) and unwraps around
`mathutils.find_normal`, which is already `g3.Vector -> g3.Vector`.

With `Vector` in and out it becomes essentially "`find_normal`, normalized" — at which point the
question is whether it should exist at all, or whether `mathutils` should grow a `unit_normal()`
(or callers should just do `find_normal(...).normalize()`).

**The crux is caller impact, and it must be measured before deciding.** Read how `demo22a`/`demo23`
build their mesh vertices and consume the normal:

- if the triangle corners are already `Vector`, passing them in is a clean win;
- if they are tuples or numpy rows, and the normal ends up in a `np.float32` vertex buffer or a
  `glNormal3f` call, then `Vector` in/out may just **relocate** the conversions to the call sites
  rather than remove them. Quantify which before touching it.

Note gacalc's `Vector` has no `__getitem__`, so any caller that indexes the normal (`n[0]`) would
need `.x`/`.y`/`.z` or unpacking. *Recommend: measure first; if the conversions only move, leave it
alone and say so in the docstring.*

**Vocabulary note:** the original task called the type `Vector3D` and the file
`src/modelviewprojection/shading.py`. Both are pre-migration names — the type is
`gacalc.g3.Vector` (mvp's own `Vector3D` was deleted 2026-07-09; gacalc dropped the dimension
suffix in 0.0.16) and the file moved to `util/shading.py` in the 2026-06-03 restructure.

## Constraints / gotchas (apply to all four)

- **New import:** `from gacalc.measure import area, signed_area` in `mathutils.py`. mvp already
  depends on gacalc, so this is a new module import, not a new dependency.
- **All of these are autodoc-published and doctested** — `sine`/`abs_sin`/`cosine` assert `1.0`,
  `0.0`, `-1.0`, `NaN`, and `_face_normal` has three doctests including the degenerate-triangle
  case. `signed_area`/`area` return the same numbers, so `float()` keeps them green — but run them.
- **Preserve the teaching comments.** The rotate-90 explanation in `sine` is pedagogy, not clutter.

## Verify

`make format` green; the `mathutils` and `util/shading` doctests pass; `make test` green; the book
still builds (`api.html` regenerates); spot-check a graph-paper figure that uses `sine`/`cosine`.

## Open questions

1. **`sine` → `signed_area`?** *(Rec: yes, keeping the rotate-90 comment.)*
2. **`abs_sin` — rewrite via `area` and keep, or delete as production-dead?** *(Rec: rewrite and
   keep; it is public, documented API.)*
3. **`_face_normal` — Vector in/out, drop it for a `unit_normal` helper, or leave it tuple-typed?**
   *(Rec: measure the `demo22a`/`demo23` call sites first; leave it alone if the conversions only
   move.)*

## Related

- gacalc `tasks/archive/2026/08/24/area-volume-content.md` — the measure work these named functions
  came from (`area`/`signed_area`/`volume`/`content`); the durable notes are gacalc's
  `tasks/reference/content-area-volume.md`.
- `tasks/archive/2026/05/26/shading-use-vector3d.md` — the earlier pass that made `_face_normal`
  compute via `find_normal` but deliberately kept tuple in/out.
- `tasks/archive/2026/08/31/use-gacalc-cross.md` — `find_normal`'s own body became
  `(p2 - p1).cross(p3 - p1)`; the same "speak the shared vocabulary" move, one level down.
