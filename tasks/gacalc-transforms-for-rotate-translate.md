# Replace hand-written rotate/translate/scale matrices with gacalc transforms

**Status:** proposed — study & discuss first, no decision yet (maintainer, 2026-09-03)
**Priority:** 5
**Difficulty:** 5

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

1. **Matrix mode vs direct mode per site** — for the renderer's `uModel` path, do you want gacalc→matrix (one
   source of truth, small conversion cost per draw), or leave the renderer's numpy matrices and only move the
   *game-logic* point math to direct gacalc vectors? *(Recommendation pending the transform→matrix finding.)*
2. **GL-1.x path** — `renderer_gl1.py` uses immediate-mode matrix ops; is it in scope, or focus on the GL-3.3 core renderer?
