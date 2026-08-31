# ty 0.0.72 strictness sweep — 74 new errors from the toolchain, not from code changes

**Status:** proposed — needs go-ahead (and one decision: the glClear fix touches published book regions)
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

## Open questions

1. **glClear + opaque `Constant`** — pick one: (a) append a bare `# ty: ignore` per site
   (RECOMMENDED: keeps the real GL idiom in the book listings; bare rather than rule-coded
   because the coded form pushes the line past the book's 80-col limit); (b) one shared named
   constant (decide-once, but hides the GL bits from the teaching listings); (c) disable the
   `unsupported-operator` rule (too blunt — loses real errors elsewhere).
2. **The gacalc-generics class** — approve filing a gacalc typing task (factories/`compose`/
   `to_matrix` bind precise `V`; ships as 0.0.19; mvp keeps its precise annotations)?
   RECOMMENDED. The mvp gate stays red on those ~25 until that lands.
