# Fully static-type all repo Python — annotate every local variable

**Status:** COMPLETE for the agreed scope — every local in `src` + `tests` carries an explicit
annotation, `make type-check` is green end-to-end (ty 8/8, the local-annotation checker at zero),
and 104 tests pass. `ports/**` is exempt (faithful-port code). Not archived this session at the
maintainer's request.
**Priority:** 6
**Difficulty:** 7
**Started:** 2026-09-16 (William Emerison Six <billsix@gmail.com>)
**Finished:** 2026-09-17 (William Emerison Six <billsix@gmail.com>)

## BLUF

Every local variable in every in-scope `.py` carries an **explicit** type annotation, not just an
inferred one — extending the already-complete parameter/return sweep so the codebase is fully,
visibly statically typed. Done = the repo-wide gate reports zero un-annotated local bindings across
the agreed scope, `ty` stays green, and the suite passes. Requested 2026-09-16: "make sure all
python source in this repo has static types, all local variables, everything."

## Context

- **Signatures were already done.** `tasks/apply-python-coding-standard.md` drove the
  parameter+return sweep to 0 across `src/` and wired `ty check` (src/tests/ports) into
  `entrypoint/format.sh`. This task added the next layer — local variables — which that sweep did
  not touch.
- **The enforcement gap (the crux).** Nothing off-the-shelf requires local annotations: `ty`
  *infers* local types and never demands one, and ruff's `flake8-annotations` (`ANN`) rules cover
  function signatures only. So "all locals are typed" cannot be verified by the existing gate — it
  needed a custom AST check (built here).
- Standard: `~/.claude/reference/python-coding-standard.md` ("annotate generously"). The
  externally-defined-name exemption is about signatures/names we don't own and does not apply to
  locals (locals are ours to annotate).

## Decisions

- **Scope (Q1).** ALL repo Python, book demos included. The initial proposal exempted the
  student-facing `demoNN` demos and `assignments/` as procedural teaching code, but the maintainer
  overrode it ("I want all python typed … all local variables, everything"). Final in-scope set:
  `src` (library + `mvpvisualization` + `cayley` + `pgzero_gl` + `util` + `plotsforbook` + `wxapp*`
  + the `demoNN` book demos) and `tests`. **`ports/**` is exempt** — 2148 locals of behaviour-
  faithful port code (openglsuperbible v4 + code-the-classics), the same faithful-port category the
  gacalc sweep exempts; annotating them would be huge low-value churn. Confirmed by the maintainer
  2026-09-17: "leave ports alone." (`ty` still *runs* on `ports/codetheclassics`.)
- **Enforcement (Q2).** Built `tools/check_local_annotations.py` — a pure-stdlib AST checker that
  flags any plain `name = ...` inside a function whose `name` is never annotated in that function.
  It lives in **`make type-check` only, not `make format`** (maintainer's call 2026-09-17), so the
  annotation rule is enforced and can't silently regress, without slowing the everyday format pass.
- **Un-annotatable targets (Q3).** The checker exempts what can't carry an inline annotation or
  isn't a local: tuple/list-unpack targets, attribute/subscript targets, augmented assignment,
  `for` / `with as` / `except as` / comprehension / walrus targets, module-level assignments, and
  (after a fix, below) class-body assignments. Annotating a name once per function covers all its
  later re-binds, so only the first occurrence is annotated.
- **Pedantry (Q4).** Every simple local is annotated, trivial ones included — that is what the
  checker enforces.

## What was done

- **The gate.** `make type-check` runs `ty` over src/tests/ports plus
  `tools/check_local_annotations.py src tests`. Green end-to-end at completion.
- **The sweep**, baseline 519 un-annotated locals in `src` + 25 in `tests` → **0**. Order of the
  push: `mvpvisualization/*` (perspective demo, cayley_gl, _pipeline, model, pushmatrix, modelview,
  modelview2d, modelvieworthoprojection, coordinatesystems) → `cayley/*` → `matrix_stack.py` +
  `mathutils.py` → `demos/demo21` → book demos `demo22/22a/23/24` → the final parallel push
  (demos stragglers demo03/17/18/19/19e, `framebuffer/softwarerendering`, `util/*`, `pgzero_gl/*`,
  `plotsforbook/*`, `wxapp`/`wxapp2`) and `tests`.
- **Checker fix during the sweep.** `check_local_annotations.py` was filtering only nested
  def/lambda scopes out of a function's own scope, so it wrongly flagged class attributes / **Enum
  members** of a class defined inside a function (`world = auto()` in `test_cayley_graph.py`) as
  locals — annotating those would change their meaning. It now also filters `ClassDef` subtrees;
  such a class's methods are still checked by the top-level walk.

### Notable type decisions

- **GL constants are not `int`.** A bare `GL.GL_*` constant assigned to a local uses the
  `_pipeline` `GLenum` (`int | Constant`) alias, not `int` — ty caught three `GL.GL_*`-into-`int`
  mismatches in demo24.
- **Documented `typing.Any`** for genuinely opaque library types: glfw's `GLFWvidmode` return
  (ty infers it but it can't be named), miniaudio's C-binding returns, and gacalc's internal `Coef`
  (`int | float | sympy.Expr`, in `shading.py`). Each carries a trailing comment naming the real
  type.
- **TYPE_CHECKING imports** for types only used in annotations (glfw `_GLFWmonitor`, ctypes
  `_Pointer`, pygame-shim `Renderer`, `ModuleType`), safe because `from __future__ import
  annotations` makes local annotations non-evaluated.
- `np.ndarray` for numpy arrays; `importlib.machinery.ModuleSpec | None` for
  `spec_from_file_location`; wx.* types throughout the wx apps (no `Any` needed there).
- **One behaviour-preserving restructure:** `pgzero_gl/resources.py` had a chained assignment
  (`res = self._cache[name] = self._make(p)`, un-annotatable), split into three lines so the local
  could be annotated.

### Method

The fast loop: run `check_local_annotations.check_file` on a file, annotate the first flagged
occurrence of each name with a per-file name→type map, repeat to converge (handles same-function
re-binds and multi-function reuse), then `ruff check --fix` + `ruff format`, then the container
gate for `ty`. The final push fanned the remaining packages out to parallel per-package subagents
(disjoint files), each making the checker report zero + local ruff, followed by one container
`make format`/`make type-check`/`make test` pass to verify and fix residuals. Committed as one
contiguous typing block, one commit per package.

## See also

- `tasks/apply-python-coding-standard.md` — the signature (param/return) sweep this extends.
- `~/.claude/reference/python-coding-standard.md` — the shared standard ("annotate generously").
