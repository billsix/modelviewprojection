# ty 0.0.72 strictness sweep — 74 new errors from the toolchain, not from code changes

**Status:** DONE + ARCHIVED 2026-09-06 — `make format` exits 0 under ty 0.0.74 + gacalc 0.0.19 (image rebuilt for the pin); the 36 invariance errors cleared with the pin, and the only fallout was two now-unused blanket `# ty: ignore`s on demo07's `@` compositions (removed; ruff reflowed the two book lines). 104 tests.
**Priority:** 3
**Difficulty:** 5
**Created:** 2026-08-31

## BLUF

The 2026-08-31 image rebuild (for the gacalc 0.0.18 bump) pulled **ty 0.0.72**, which is
stricter than the ty the last green gate ran under: `make format`'s ty half now fails with
**74 errors across ~25 files**, nearly all untouched by the 0.0.18 work (verified: the three
hits in touched files are all pre-existing lines). Ruff, `make test` (104), and
`make check-regions` stay green. Done means `make format` is fully green again under 0.0.72.

## Context

- Full log: captured at the time in the session scratchpad; regenerate with `make format`.
- Error classes (by count):
  - **54 × `no-matching-overload` — `GL.glClear(sum([GL.GL_COLOR_BUFFER_BIT, ...]))`**
    across demos 01–23: new ty rejects `sum` over PyOpenGL `Constant`s. The idiomatic fix is
    the bitwise `GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT` — **but these lines sit in
    published book doc-regions**, so the fix changes chapter listings (and arguably teaches
    the better idiom). Maintainer decision required: change code+book, or suppress.
  - **`invalid-argument-type` invariance errors** — e.g. `tests/test_mathutils.py` passing
    `InvertibleFunction[Vector]` where gacalc's `to_matrix` takes
    `InvertibleFunction[MultiVectorBase]` (invariant generic). Fix side unclear: a
    `to_matrix` signature generalization belongs in gacalc; a cast belongs here.
  - `mathutils.py:440` `compose` overload complaint (the `ortho` internals);
    `generate_plots.py` (9); `wxapp*.py` (3); ports: 5 total incl.
    `vol2/eggzy` `game.time_remaining += time * 60` (`float` into an int-typed field).
- **Not caused by gacalc 0.0.18**: the errors are spread across files with no gacalc-surface
  change; the tool version is the variable (fresh dnf/pip in the rebuilt image).

## Triage after the first fix round (2026-08-31, later the same day)

- **House precedent found:** `tasks/archive/2026/07/09/src-ty-diagnostics-after-ty-bump.md` —
  the identical situation (Fedora ty bump → 79 diagnostics) was resolved by **fixing the code,
  never pinning ty**, and the gate was hardened afterward. Follow that here.
- **glClear: the approved `sum→|` conversion is DONE (37 sites, 35 files, staged) but trades
  error classes** — ty 0.0.72's PyOpenGL stubs make `Constant` fully opaque: no `__or__`, no
  `__int__`/`__index__`, not assignable to `int` (all verified against ty in-container), so
  `A | B`, `int(A) | int(B)`, and an int-annotated constant ALL fail the checker while being
  fine at runtime (`IntConstant` subclasses `int`). Still 74 errors total.
- **The demos-06–18 class (~25 errors) is gacalc's to fix:** ty now strictly enforces what the
  signatures say — the scalar-argument factories (`uniform_scale(m=…)`, `scale_non_uniform`)
  have no vector argument to bind `V`, so they return `InvertibleFunction[MultiVectorBase]`,
  which invariance won't assign to the demos' precise `InvertibleFunction[Vector]`
  annotations; same family: `compose` overloads, `@`, `to_matrix`, `tests/test_mathutils.py`,
  `generate_plots.py`. Proper fix = a gacalc typing release (0.0.19): make those factories/
  `compose`/`to_matrix` bind or accept the caller's precise `V`. Loosening mvp's annotations
  instead would surrender the checker-precision the course deliberately teaches with.
- **Singles** (ordinary code fixes once the above are decided): `eggzy.py:1619` (`float` into
  an int-typed `time_remaining`), `bunner.py:811`, `beatstreets.py:640`, `notebooksrc/ndc.py`,
  `wxapp*.py` (3).

## Open questions (both settled: Q1 by the maintainer 2026-09-05 — bare `# ty: ignore`; Q2 yes — filed, shipped as gacalc 0.0.19)

1. **glClear + opaque `Constant`** — pick one: (a) append a bare `# ty: ignore` per site
   (RECOMMENDED: keeps the real GL idiom in the book listings; bare rather than rule-coded
   because the coded form pushes the line past the book's 80-col limit); (b) one shared named
   constant (decide-once, but hides the GL bits from the teaching listings); (c) disable the
   `unsupported-operator` rule (too blunt — loses real errors elsewhere).
2. **The gacalc-generics class** — approve filing a gacalc typing task (factories/`compose`/
   `to_matrix` bind precise `V`; ships as 0.0.19; mvp keeps its precise annotations)?
   RECOMMENDED. The mvp gate stays red on those ~25 until that lands.

## Progress (2026-09-05, later same day)

Ran the gate under **ty 0.0.74** (image rebuild); 71 diagnostics. Resolved the two mvp-owned
classes; the rest is gacalc's:

- **glClear (34 sites) — DONE, maintainer chose bare `# ty: ignore`** (idiomatic GL `A | B`,
  PyOpenGL's `Constant` is opaque to ty — verified: `sum`, `A|B`, `int(A)|int(B)` all fail; a
  bare ignore keeps the 4-space demo lines at 77 cols, in-book). 31 demos got the inline bare
  ignore; **3 deep-indent (8-space) sites** (`wxapp.py:185`, `wxapp2.py:170`,
  `mvpvisualization/cayley_gl.py:662`) became a `mask = A | B  # ty: ignore` local + `glClear(mask)`
  (76 cols) since inline would hit 81 → E501. Two **pre-existing rule-coded** ignores
  (`demo22.py:701` at 99 cols, `cayley_gl.py:662`) normalized to the chosen form. **E501 = 0.**
- **`wxapp2.py:129` `rotation_angle = 0` → `0.0`** — the one genuine `invalid-assignment` (float
  accumulates into an int-inferred attr; runtime already rebinds to float, so behavior unchanged).
- **Result: 71 → 36.** ruff fully green, `make test` 104 passed. The remaining **36 are all the
  gacalc-invariance class** (22 `compose` no-matching-overload, 11 `to_matrix`/`create_graphs`
  invalid-argument-type, 3 `uniform_scale` invalid-assignment).
- **The 36 are blocked on gacalc 0.0.19** — task filed AND being implemented:
  `github.com/billsix/geometricalgebra` `tasks/ty-invariance-transform-factories-bind-v.md`. When
  that ships, bump the mvp pin and the 36 clear; then `make format` is fully green and this task
  archives.

## Completion record (2026-09-06, Fable, overnight)

- `make image BUILD_DOCS=0 USE_EMACS=0 USE_JUPYTER=0 USE_SPYDER=0` with the 0.0.19 pin (ty 0.0.74
  inside); `make format` → the 36 gacalc-invariance errors are gone (`uniform_scale`/`scale_non_uniform`
  bind `[V]`, `to_matrix`/`compose` accept the precise `V`), leaving 2 warnings: unused blanket
  `# ty: ignore` on `src/modelviewprojection/demos/demo07.py:151` and `:169` (the `@` compositions the
  0.0.18 overloads rejected). Removed; `make format` exit 0; 104 tests.
- The maintainer's rebuild with the default flags (`make image`, docs on) is still owed by whoever runs
  it next — the ty/ruff half of the gate does not depend on the docs flag.
