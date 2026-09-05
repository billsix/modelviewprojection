# Replace hand-written rotate/translate/scale matrices with gacalc transforms

**Status:** STUDIED 2026-09-04 (findings below; NO decision or implementation, per the task's own instruction). **Crux answered: gacalc has a built-in `to_matrix` bridge.** Recommendation: the *direct-path* (game-logic point math) is already largely done via gacalc; **leave the renderer's `uModel` matrices as-is**. Awaiting maintainer discussion.
**Priority:** 5
**Difficulty:** 5

## Findings (2026-09-04, study executed — for discussion, nothing changed)

### The crux is answered: YES, gacalc has a clean transform→matrix bridge

`gacalc.transforms.to_matrix(fn, cls, n=None, *, backend="numpy")` (verified in the mvp container):
- Returns the **homogeneous (n+1)×(n+1)** matrix of a linear/affine `fn` — **3×3 in 2-D, 4×4 in
  3-D**, always homogeneous (a linear map gets a zero translation column: "one uniform shape for
  the whole stack").
- **Translation in the last column — column-vector / premultiply convention, which its own
  docstring says matches mvp's `matrix_stack`.** So it drops straight into the GL `uModel` upload.
- `backend="numpy"` → `np.float32` array (GL-ready); `backend="sympy"` → exact symbolic matrix.
- Built by **probing the basis + origin** internally (the standard GA→matrix technique — I
  reproduced it by hand and got identical results for translate / scale / a pseudoscalar 90°).
- **Raises `ValueError` on a non-linear `fn`** — a perspective divide (leadingedge) can't be
  recovered by probing points, so it correctly refuses. (Consistent with leaving that projection
  hand-rolled, as done in `tasks/archive/2026/09/05/codetheclassics-leadingedge-projection-functions.md`.)

So mode (a) "gacalc transform → 4×4 for GL" needs **no basis-sampling of our own** and no bespoke
bridge; it's one call, in mvp's convention.

### Inventory — matrix-path vs direct-path (verified 2026-09-04)

- **Matrix-path (feeds `uModel`)** = the renderer only: `src/modelviewprojection/pgzero_gl/renderer.py`
  `_identity`/`_translate`/`_scale`/`ortho_pixels` and `model = _translate(...) @ _scale(...)`
  (`:227`, `:253`), inlined into all **10** games. **It is translate + non-uniform scale only —
  there is NO rotation in `uModel`** (sprites are axis-aligned; the task's earlier "`_rotate_z`"
  note was inaccurate — `:66` is `ortho_pixels`, and no rotation helper exists). `boing_gl1.py`
  uses the fixed-function equivalent (`glTranslatef`/`glScalef`/`glOrtho`).
- **Direct-path (CPU point math)** is **already largely gacalc**, and today's work advanced it
  further: rotations via `myriapod` `* e_12` and `kinetix` `plane_rotation`/`_turn`; camera/scroll
  via `soccer`/`leadingedge`/`beatstreets` `inverse(translate(...))`. So the "make game logic use
  gacalc vectors + transforms" half of this task is mostly done in passing.

### Recommendation (options for you — not decided)

1. **Direct-path: keep going as opportunity arises** — it's already the pattern; convert any
   remaining hand-rolled point math to gacalc vectors/transforms case by case. Low risk, high
   clarity, no perf concern (CPU-side, once per object).
2. **Matrix-path (renderer `uModel`): LEAVE the hand-written numpy `translate @ scale` as-is.**
   Reasons: (a) it's a **per-sprite-per-frame hot path**, where a `to_matrix` probe-the-basis
   build per draw adds real cost for a *trivial* translate+scale; (b) the repo `CLAUDE.md`
   deliberately keeps the renderer at the `glUniformMatrix4fv` boundary matrix-based; (c) there's
   **no rotation** in `uModel`, so gacalc's real win (clean rotation composition) doesn't apply
   here. The `to_matrix` bridge is proven and available **if a future need arises** (e.g. rotated
   sprites) — and it would match mvp's convention exactly, so adopting it later is cheap.

**Net:** the interesting half (game-logic direct-path) is largely handled; the renderer's matrix
path is best left alone. If you want a single source of truth *badly enough* to pay the per-draw
cost, `to_matrix` makes it a one-liner — but I'd only do that if the renderer gains rotation.

## BLUF

The `pgzero_gl` renderer (and some Code-the-Classics game logic) builds rotate/translate/scale as **hand-written
numpy 4×4 matrices**, while `gacalc.transforms` already expresses the same operations as `InvertibleFunction`s
(and the maintainer's demos apply them directly to `gacalc` `Vector`s). The idea: **express these transforms as
gacalc calls**, used **either way** — (a) **converted to a 4×4 matrix** for the GL `uModel` pipeline, or
(b) **applied directly** to `gacalc` vectors for CPU-side point math (sprite motion, velocity rotation). This
would make gacalc the single source of truth for the transform math instead of two parallel implementations.
**This task is to STUDY it and talk it through — do NOT decide or implement yet.**

## Context (verified 2026-09-03)

- **The shim's matrices** (`src/modelviewprojection/pgzero_gl/renderer.py`): `_translate(x, y)` (`:50`),
  `_rotate_z(degrees)` (`:66`, cos/sin), `_scale(sx, sy)`; composed as `model = _translate(...) @ _scale(...)`
  (`:246`) and with rotation (`:251`), then uploaded via `glUniformMatrix4fv(self.u_model, …)` (shader `uModel`,
  `:107`). `renderer_gl1.py` likely does the GL-1.x equivalent (immediate-mode matrix ops).
- **gacalc.transforms** (`geometricalgebra/src/gacalc/transforms.py`): `translate(b)` (`:148`),
  rotation constructors (`rotor_rotation`, `bivector_rotation`, `plane_rotation`, `projection_rotation`),
  `uniform_scale(m)` (`:518`), `scale_non_uniform(*factors)` (`:552`), and `compose_intermediate_fns` — each an
  `InvertibleFunction[V]` operating on vectors/multivectors. The demos (demo05-08, demo22) already
  `from gacalc.transforms import translate, uniform_scale` and apply them to `gacalc.g2`/`g3` `Vector`s directly.
- **This is a facet of the broader pgzero_gl study** — see
  `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md` (the design study) and
  `tasks/pgzero-gl-de-abstraction-options.md` (its option menu). That study steers toward **"direct mode for
  actor/game math, leave the renderer's `uModel` matrices as-is"** (the renderer is the `glUniformMatrix4fv`
  boundary the repo `CLAUDE.md` keeps matrix-based) — but this task deliberately leaves that open for discussion.

## The key question to study (the crux of the discussion)

**Does gacalc offer a clean `InvertibleFunction`/transform → 4×4 matrix conversion, or not?**
- The demos apply gacalc transforms **directly to vectors** (CPU-side) — no matrix. That path is proven.
- The GL `uModel` uniform needs a **4×4 matrix**. So mode (a) needs a transform→matrix bridge. Options to
  investigate: (i) gacalc already has a "to matrix" facility; (ii) build the matrix by **applying the transform
  to the basis vectors** (e_1, e_2, origin) and reading off columns — a standard GA→matrix technique;
  (iii) keep the GL matrix build in the renderer but generate it *from* a gacalc transform spec so there's one
  source of truth. Determine which is real + clean.
- Then: which sites want **matrix mode** (the renderer's per-quad `uModel`) vs **direct mode** (game logic that
  moves/rotates points and doesn't need a GL matrix at all — those should just use gacalc vectors + transforms,
  no matrix).

## What to bring back to the discussion (no decision here)

1. An inventory of every hand-written rotate/translate/scale matrix + manual rotation math in the shim AND the
   games (`file:line`), tagged **matrix-path** (feeds `uModel`) vs **direct-path** (CPU point math).
2. The transform→matrix story: does it exist in gacalc, or must we sample basis vectors? A tiny worked example.
3. A recommendation split by site (which to convert, which to leave), with the clarity/perf trade-offs — but as
   options for the maintainer to choose, not a done decision.

## Open questions (for the maintainer, after the study)

1. **Matrix mode vs direct mode per site** — for the renderer's `uModel` path, do you want
   gacalc→matrix (one source of truth via `to_matrix`, a probe-the-basis cost per draw), or leave
   the renderer's numpy matrices and only keep the *game-logic* point math on direct gacalc
   vectors? *(Recommendation now IN — see Findings: **leave the renderer matrices**; the
   direct-path is already largely done. `to_matrix` exists and is clean, but the renderer is a
   trivial rotation-free hot path where it doesn't earn the per-draw cost.)*
2. **GL-1.x path** — `renderer_gl1.py` / `boing_gl1.py` use immediate-mode `glTranslatef`/`glScalef`;
   same recommendation as the 3.3 renderer (leave as-is — it's the fixed-function boundary, no
   rotation). *(Recommend: out of scope for conversion.)*
