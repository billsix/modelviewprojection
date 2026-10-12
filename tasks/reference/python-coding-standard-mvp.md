# Python coding standard — modelviewprojection-specific additions

**Reference document.** modelviewprojection's own rules and worked examples that specialize
or extend the shared cross-project Python standard. Read this *together with* the shared doc
`runClaudeInContainer/tasks/reference/python-coding-standard.md` (canonical:
github.com/billsix/runClaudeInContainer; mounted at `~/.claude/reference/python-coding-standard.md`):
the shared doc holds the portable rules, this doc holds mvp's specializations, file paths,
framework names, and worked examples. Moved out of the shared doc on 2026-10-12 so that doc
stays portable (William Emerison Six <billsix@gmail.com>). Update in place.

## Line length is 80, because the book is a PDF

Unlike the 88-column default in the shared doc, mvp sets **`line-length = 80`** in
`pyproject.toml`, which governs both the formatter and E501 — 80 because the book is built as
a PDF, where wider lines wrap badly or run off the page. Everything else in "Line length is
the formatter's job" still applies: write the clearer form and let `ruff format` wrap it.

## Every `per-file-ignores` entry carries its reason in `pyproject.toml`

Read them before "fixing" a flagged name — most are deliberate.

## An externally-defined name overrides the naming rules — mvp's wx boundary

Applying the shared "An externally-defined name overrides the naming rules" rule: here that is
`wxapp.py` / `wxapp2.py` (`OnPaint`, `OnTimer`, `InitGL`, `OnDraw`, `OnInit` — wx looks
up those exact names; exempted from `N802` only) and wx's `attribList=` keyword. The
exemption covers only the fixed name: locals inside those methods follow house style
(hence `VBO` -> `vbo`, `attribList` -> `attrib_list` at the local).

## Python naming wins over the book's mathematical shorthand — everywhere, including the demos

The chapters' Cayley-graph edges are labelled in vector notation
(`\vec{R}_<θ>`, `\vec{T}_<x,y>`, `\vec{S}_<s>`) and the demos used to alias
`translate as T` / `rotate as R` / `uniform_scale as S` to match, with frustum bounds
as `L,R,B,T,N,F` and a light position as `Lx,Ly,Lz,Lw`. **All of that is spelled out
now**: `translate()`, `rotate()`, `uniform_scale()`, `left/right/bottom/top/near/far`,
`light_x…light_w`.
**The graph-to-code mapping is what makes this safe, so keep it.** Each affected demo
carries a short comment above its imports reading the graph labels off against the
function names. When you add a demo whose chapter has a diagram, add the same note —
a student must be able to line the picture up with the source without guessing.
The single remaining naming exemption is `N813` for `import … matrix_stack as ms`,
and it is temporary: the fix is renaming the camelCase *module*
(`tasks/archive/2026/07/19/rename-pymatrixstack-module.md`), which deletes the exemption at the source
rather than suppressing it.

## `translate`/`uniform_scale` are called by keyword — `f(x) = m·x + b`

Call gacalc's `translate` and `uniform_scale` with their keyword names —
`translate(b=…)`, `uniform_scale(m=…)` — to make the line-equation reading explicit
(the parameters are named `b`/`m` in gacalc). All 88 first-party call sites were converted
2026-10-12. **Not** `scale_non_uniform`/`rotate` (no `m·x+b` reading), and **not** the
four-arg fixed-function `matrix_stack.translate(matrix_stack, x, y, z)`, which is a different
function and stays positional.

## Composition style: `f @ g` inline, `compose([...])` when it wraps

`f @ g` only when the chain fits on one line; `compose([f, g, ...])` the moment it would
wrap — same order (`f` after `g`, last listed applied first), one function per line, instead
of the formatter's dangling `@` with exploded arguments (maintainer, 2026-09-06). numpy's
matrix `@` (the `mvpvisualization` demos, `test_cayley_scene`) is not composition and keeps `@`.

## Worked example — the `match` + `case _` that was actually bitten

`matrix_stack.get_current_matrix` was five `if`s with no `else`, annotated `-> np.ndarray`,
and fell off the end returning `None` for any unhandled `MatrixStack` member — while every
caller indexed the result. It is now a `match` with `case _: raise`. See also `_route` in
`cayley/cayleygraph.py`, whose tail is a three-case `match`, and `cayleygraph._DfsColor` (an
`enum.IntEnum` that replaced a bare `WHITE, GRAY, BLACK = 0, 1, 2`).

## Inner-function-first — mvp's own verified precedents

The shared "What earns an extraction" rule uses gacalc's `base.reject` as its worked example;
`base.reject` does not exist in mvp. mvp's own instances of the shape — inner function(s) up
top closing over the enclosing parameters and naming a phase, dispatch/guards below calling
in — both live in the Cayley-graph engine and were re-read to confirm they illustrate the
rule, not its opposite (William Emerison Six <billsix@gmail.com>, 2026-10-12):

- **`CayleyGraph._route` (`src/modelviewprojection/cayley/cayleygraph.py`).** Two inner fns,
  `breadth_first_parents` and `walk_back`, close over `a`/`b`; a `match (a, b)` below handles
  the empty and unknown-endpoint cases, then calls them. It also shows the corollary —
  *raise the error from the code that discovers it*: `breadth_first_parents` raises
  "no path" itself, which is what lets the dispatch tail stay short.
- **`CayleyGraph._assert_acyclic` (same file).** Builds the directed-adjacency and `color`
  maps, then an inner `visit(n)` closes over both and recurses (the DFS-3-colouring phase);
  the driver loop below calls `visit`, and the cycle error is raised from inside the
  recursion that finds it.

**Not this rule, so do not cite them as precedents:** the `f`/`f_inv` inner fns in
`mathutils.ortho`/`perspective` are `InvertibleFunction(func=…, inverse=…)` callback wrappers
— named only because that API takes callables, not extracted phases.

## OpenGL / PyOpenGL typing and matrix conventions

A GL concern for annotation specifically: **a GL enum is a PyOpenGL `Constant`, not an
`int`** — do not annotate `GL.GL_TRUE` etc. as `int` (the live `ty` diagnostic at
`pgzero_gl/runner.py:72` is this); the uninitialised-uniform sentinel is `-1`; matrices
upload **row-major with `GL_TRUE`**; winding is CCW. These, plus import order and the
GL-resource registry, are in `tasks/reference/gl-and-imgui-gotchas.md` (§7 conventions,
§§1–6 failure modes).

## The gacalc vector dialect, and vectors are frozen

Transform/vector code uses gacalc's spelling (`magnitude` not `length`, `scalar_product` not
`dot`, `plane_rotation` for a degree rotate, `f @ g` / `compose([…])` for composition — see
`tasks/reference/code-the-classics-tightening.md`). **gacalc vectors are frozen:** change a
coordinate by rebinding, never in place — `ty` catches `v.x = …` but **not** `v.x += …`, so a
grep for `\.(x|y|z)\s*[-+*/]?=` is part of any audit after a bulk vector edit.

## Behaviour-faithful ports: structure may change, observable behaviour may not

For `ports/` one constraint the first-party rules don't carry: applying house style (naming,
annotations, `match`, extraction) is allowed and expected, but it must not change *observable
behaviour* — same RNG, update/draw order, and output. The gates that pin this are
`tools/ctc_verify_game.sh` (frame pixel identity vs a git ref) and the scripted state-trace
tools; see `tasks/reference/code-the-classics-tightening.md` and
`tasks/reference/tests-and-gates.md`. A port refactor is judged by *both* the style rules and
a behaviour gate, and the gate wins.

## New code vs existing code

These shapes apply to *new* code; working code is not rewritten to chase them. (The
2026-07-18 sweep that brought the tree into compliance was a deliberate one-time exception,
not the ongoing rule.)

## Duplication across `demos/` is deliberate — "teach once, then share"

A demo may re-inline a helper when its chapter teaches it; `util/clipping.py`,
`util/windowing.py` and `util/cameracontrols.py` document their own cases. Do not DRY the
~20 near-identical `Paddle`/`Camera` dataclasses without reading those notes.
