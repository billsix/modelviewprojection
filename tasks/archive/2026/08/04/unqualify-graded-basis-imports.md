# Import unqualified graded basis constants (e_1, e_2, …) instead of `Vector2.e_1`

**Status:** done (2026-08-04)
**Priority:** 5
**Difficulty:** 3

## Goal

mvp's teaching code reached basis vectors through the class — `Vector2.e_1`,
`Vector3.e_3`, etc. Drop the repeated `Vector2.`/`Vector3.` prefix so the code reads as
concise as the printed math (`3 * e_1 + 4 * e_2` ↔ `3e₁ + 4e₂`), while staying
`Vector2`/`Vector3`-typed.

## Unblocked by gacalc 0.0.15 (was blocked in the 2026-08-04 investigation)

The earlier finding (below, kept for history) was correct **for gacalc ≤ 0.0.14**: there
`from gacalc.g2 import e_1` yielded a `G2`, not a `Vector2`, so an unqualified import
silently changed the type. **gacalc 0.0.15 fixed this** — the module-level constants are
now the graded types:

- `from gacalc.g2 import e_1` → `Vector2`; `e_12` → `Bivector2`.
- `from gacalc.g3 import e_1/e_2/e_3` → `Vector3`; `e_12/e_13/e_23` → `Bivector3`;
  `e_123` → `Trivector3`.

Verified the module constants are the *same objects* as the class attributes
(`gacalc.g2.e_1 == Vector2.e_1`, etc.), so the conversion is provably value- and
type-neutral. Both pins were already at 0.0.15 (`requirements.txt` line 3;
Dockerfile `ARG GACALC_VERSION=0.0.15`).

## What was done — the sweep

**545 basis-constant occurrences converted across 19 files** (`Vector2.e_1` → `e_1`,
`Vector3.e_3` → `e_3`, …; the needed bare names added to each file's
`from gacalc.gN import …` line, class import kept for constructors/annotations):

- **Pure-𝒢₂ (14 files), import `Vector2, e_1, e_2`:** demos 05–13,
  `util/nbplotutils.py`, `plotsforbook/generate_plots.py`,
  `framebuffer/softwarerendering.py`, `notebooksrc/ndc.py`,
  `notebooksrc/framebuffer.py`.
- **Pure-𝒢₃ (5 files), import `Vector3, e_1, e_2, e_3`:** demos 14–18.

Dropping the prefix shortened lines, so `ruff format` re-joined previously-wrapped
expressions in 4 files (demo17, demo18, `generate_plots.py`, `nbplotutils.py`) — the
intended readability win. Instance attribute access (`.coeff_e_1`) is untouched — it is
not a class-qualified basis constant.

## What stayed qualified, and why (133 occurrences)

- **𝒢₂/𝒢₃ name-collision files (kept fully qualified).** `from gacalc.g2 import e_1` and
  `from gacalc.g3 import e_1` both bind the bare name `e_1`; a file using the shared names
  (`e_1`/`e_2`/`e_12`) from *both* algebras cannot import both unqualified without
  shadowing. Only three files use both:
  - `src/modelviewprojection/mathutils.py` — 85 sites (the façade; uses 𝒢₂ + 𝒢₃ + `Bivector3`).
  - `src/modelviewprojection/notebooksrc/plot2d.py` — 23 sites (𝒢₁/𝒢₂/𝒢₃).
  - `assignments/demo02/plot2d.ipynb` — 23 sites (𝒢₂ + 𝒢₃).
  (`e_3`/`e_13`/`e_23`/`e_123` are 𝒢₃-only and never collide — the collision is only on
  `e_1`/`e_2`/`e_12`.)
- **`ports/codetheclassics/vol2/kinetix/kinetix.py`** — 2 sites, out of scope (a
  behaviour-faithful Code-the-Classics port, not teaching code).
- **Constructors / classmethods** — none needed keeping in the swept files: no
  `Vector2(...)`-as-basis, no `Vector2.project/reflect/reject/rotor_from_vectors`, and no
  `Bivector*`/`Trivector*` basis constants appear outside `mathutils.py`. The class import
  (`Vector2`/`Vector3`) stays in every swept file because it is still used for constructors
  and type annotations.

## Verification (against gacalc 0.0.15)

- **ruff check** — clean on all 19 touched files.
- **ruff format --check** (line-length 80) — clean (19 already formatted after the reflow).
- **ty** — the sweep is type-neutral: `ty check` diagnostics are **byte-identical**
  before vs after the change (verified by stashing and re-running under the same
  `--python /usr/local`). The absolute diagnostic count is nonzero only because of the
  sandbox's split environment — distro packages (glfw/OpenGL/numpy) live in `/usr`, pip's
  gacalc in `/usr/local`, and `ty` can point at only one prefix, so the other's imports go
  unresolved. That is the `/usr` vs `/usr-local` caveat, not anything the sweep introduced.
- **py_compile** — all 19 files compile.
- **import** — the three non-GUI touched modules (`softwarerendering`, `generate_plots`,
  `nbplotutils`) import cleanly under 0.0.15. The demos import `glfw`, which is not in the
  sandbox (it is a distro package baked into the project container image), so they were
  not run headless here.
- **pytest** — see the separate blocker below; it is unrelated to this sweep.

## Blocker found during verification — NOT part of this sweep

gacalc 0.0.15 also **renamed `is_close` → `isclose` AND changed its default tolerance to
zero** (`isclose(self, other, rel_tol=0.0, abs_tol=0.0)`). mvp's test suite calls
`.is_close(other)` at 36 sites in 3 test files (`tests/test_mathutils.py`,
`tests/test_cayley_graph.py`, `tests/test_cayley_scene.py`), so `pytest` is red on master
independent of this sweep (this sweep touched no test file and no `src/` file that calls
`is_close`). A bare rename is *not* equivalent — it turns the AttributeErrors into 9
zero-tolerance float-comparison failures; the migration needs an explicit tolerance per
call site, which is Bill's call. Tracked separately in
`tasks/gacalc-0015-isclose-tolerance-migration.md`.

---

## Original finding (2026-08-04, gacalc ≤ 0.0.14) — kept for history

Checked against gacalc 0.0.14: `from gacalc.g2 import e_1` yielded a **`G2`** (the full
dimension class), not a `Vector2`; `Vector2.e_1` was the only source of the graded-typed
basis vector, and gacalc exported no `Vector2`-typed module constant. So the win was gated
on a gacalc change to export graded-typed module constants — which is exactly what 0.0.15
delivered.
