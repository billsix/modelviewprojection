# Code the Classics: use gacalc's matrix template, delete the ten `MatrixTemplate` copies

**Status:** ready — gacalc HAS the feature (`to_matrix_template` / `MatrixTemplate` + the method
forms on `ComposableFunction`, implemented 2026-09-06; record
`tasks/archive/2026/09/06/matrix-template-compile-once.md` in `github.com/billsix/geometricalgebra`).
Unblocked by the maintainer 2026-09-06 ("I'll make a release of geometricalgebra today"); step 1
below is that release + the pin bump (PyPI was at 0.0.19 when this was written).
**Priority:** 4
**Difficulty:** 3

## BLUF

Each of the ten OpenGL 3.3 game engines (`ports/codetheclassics/vol1/{boing,bunner,cavern,myriapod,
soccer}/*.py`, `vol2/{avenger,beatstreets,eggzy,kinetix,leadingedge}/*.py`; not `boing_gl1.py`,
whose fixed-function path has no matrix) carries an identical ~50-line `MatrixTemplate` dataclass and
the `MODEL`/`ortho_pixels` definitions built with it (added 2026-09-06 by the codemod `model_matrix_from_gacalc.py`, gated frame-identical; the script was removed 2026-09-06 when its task archived (one-shot; in git history under the archived task)).
Once gacalc provides the same thing, delete the ten copies and build `MODEL` with the library call;
`ortho_pixels` keeps calling `to_matrix` with numbers. Byte-identical output expected; the usual
gates apply.

## Context (read first)

- `tasks/reference/gacalc-transforms-in-the-renderer.md` — why the renderer's matrices come from
  gacalc, the numbers (0.47 µs per fill vs 3.19 µs hand-built), and the compile-once pattern the
  library version reproduces.
- The engine block to replace: search `class MatrixTemplate` in any of the ten files; `MODEL =
  MatrixTemplate.compile(compose([translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2),
  scale_non_uniform(_W, _H, 1)]), (_TX, _TY, _W, _H))` and the three/one `MODEL.fill(...)` call sites in
  `Renderer.draw_image` (+ `draw_image_region`, `filled_rect` where present).
- The archived task that put the copies there: `tasks/archive/2026/09/06/renderer-model-matrix-from-gacalc.md`.

## Plan

1. Once gacalc 0.0.20 (the release carrying `to_matrix_template`) is on PyPI,
   bump the gacalc pin (`requirements.txt` + the Dockerfile's `GACALC_VERSION`), `make image`.
2. A small idempotent codemod under `tasks/adhoc/ctc-use-gacalc-matrix-template/`: delete the
   `MatrixTemplate` class + its comment block from each engine, rewrite `MODEL = ...` to the library
   call — the method form `compose([translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2),
   scale_non_uniform(_W, _H, 1)]).to_matrix_template(g3.Vector, (_TX, _TY, _W, _H))`, or the free
   function `to_matrix_template(fn, g3.Vector, (_TX, _TY, _W, _H))` from `gacalc.transforms` — and
   drop the now-unused `dataclass`/`Sequence`/`sympy`/`NDArray` imports where nothing else uses them
   (ruff will say); keep `ortho_pixels`. The library's `fill(*values)` has the same signature and
   returns the same fresh `np.float32` 4x4 (bit-identical for this all-slots template, gated in
   gacalc's `tests/test_matrix_template.py`), so the `MODEL.fill(...)` call sites do not change.
3. Gates per file: `tools/ctc_verify_game.sh` (AE=0), the state traces, ruff + ty, pytest.
4. Reference doc: note the copies are gone and gacalc owns the template.
