# Rewrite mathutils' `sine` / `abs_sin` in terms of gacalc's named measures

**Status:** proposed — needs go-ahead. Audit done 2026-08-24 (William Emerison Six <billsix@gmail.com>),
spun out of gacalc's measure work (`github.com/billsix/geometricalgebra`,
`tasks/area-volume-content.md` / `explicit-symbolic-tests-and-helper-cleanup.md`).
**Priority:** 6
**Difficulty:** 3

## Context

gacalc (`github.com/billsix/geometricalgebra`) now has named **measure** free functions —
`area(a, b)` (= `|a ∧ b|`, unsigned), `signed_area(a, b)` (= the 2×2 determinant / signed 2D
parallelogram area, needs a fixed-dimension type), `volume`/`signed_volume`, `content`. mvp's
`src/modelviewprojection/mathutils.py` has three angle helpers that compute exactly these quantities by
hand; they can be re-expressed in terms of the named measures, which ties the book's own vocabulary to
the shared library.

## The three helpers (mathutils.py)

- **`sine(v1, v2)` (2D, signed)** — returns `float((v1 ^ v2).coeff_e_12) / (|v1||v2|)`. That numerator
  **is** `signed_area(v1, v2)` (the e₁₂ coefficient of the wedge = the 2D signed area). Verified:
  `signed_area` works on `g2.Vector` (mvp's type). **Rewrite:**
  `signed_area(v1, v2) / (float(abs(v1)) * float(abs(v2)))`, keeping the zero-length → `NaN` guard and
  the `float()` conversions.
- **`abs_sin(v1, v2)` (3D, unsigned)** — returns `float(abs(v1 ^ v2)) / (|v1||v2|)`. That numerator
  **is** `area(v1, v2)` (the magnitude of the wedge). Verified: `area` works on `g3.Vector`.
  **Rewrite:** `area(v1, v2) / (float(abs(v1)) * float(abs(v2)))`. **Also note:** `abs_sin` has **no
  production caller** — only `tests/test_mathutils.py::test_abs_sin` and the autodoc API page reference
  it. So decide: rewrite-and-keep (it's public API + book-documented), or remove it (dead in
  production). *Rec: rewrite via `area` and keep it, since it's a documented public helper; flag for
  Bill.*
- **`cosine(v1, v2)` — KEEP.** `v1.dot(v2).scalar_part() / (|v1||v2|)`, any dimension, NaN-safe. It
  parallels gacalc's base `cosine` **method** (`v1.cosine(v2)`, Hestenes & Sobczyk p. 14) but adds the
  NaN-on-zero-length behavior mvp relies on (`softwarerendering.is_parallel` uses
  `math.isclose(cosine(...), 1.0)`). The method **raises** on a zero vector instead. So do **not**
  replace `cosine` with the method — keep the NaN-safe float wrapper. (Optional: have its body call
  `v1.cosine(v2)` inside the non-zero branch, but the current `dot/|·|` form is already clear.)

## Constraints / gotchas

- **These are book-API-documented (autodoc `api.html`) and carry doctests** asserting `1.0`, `0.0`,
  `-1.0`, `NaN`. `signed_area`/`area` return the same numeric values, so wrapping in `float()` keeps the
  doctests green — but **run the doctests** (`sine`/`abs_sin`/`cosine` are in `mathutils.py`, covered by
  the doctest gate) after the change.
- **New import:** `from gacalc.measure import area, signed_area` in `mathutils.py` (mvp already depends
  on gacalc — it imports `gacalc.g2`/`g3` — so no new dependency, just a new module import).
- **Preserve the teaching comments.** mvp's `sine` already documents the "rotate 90° then dot" classic
  trick in a comment; keep that pedagogy (or point at `signed_area`) so the book still explains *why*.
  (In gacalc's own `nbplotutils.sine`, Bill chose to KEEP the rotate-90 form for teaching rather than
  switch to `signed_area` — because that helper runs on the dimensionless `Gn`, where `signed_area`
  can't apply. mvp's `sine` is typed to `g2.Vector`, which *does* have a dimension, so `signed_area`
  works here — but weigh the same teaching trade-off.)

## Verify

`make format` green; the mathutils doctests pass; `make test` green; and the book still builds
(`api.html` autodoc regenerates). Spot-check a graph-paper figure that uses `sine`/`cosine`.

## Open questions

1. **`abs_sin`** — rewrite via `area` and keep (rec), or remove it as dead production code (it's public
   API + book-documented + tested)?
2. **`sine`** — switch to `signed_area` (rec, since `g2.Vector` has a dimension so it works), or keep
   the rotate-90 teaching form like gacalc's `nbplotutils.sine`?
