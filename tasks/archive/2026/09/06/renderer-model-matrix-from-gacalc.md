# Renderer: define the sprite model matrix (and ortho) in gacalc, compiled once

**Status:** DONE + ARCHIVED 2026-09-06 — all ten GL 3.3 engines define `MODEL` and `ortho_pixels` with gacalc transforms (a `MatrixTemplate` compiled once at import); every frame gate AE=0 vs HEAD, all nine input traces identical, ruff + ty clean, 104 tests; staged. Follow-on: the ten `MatrixTemplate` copies move into gacalc itself — `tasks/ctc-use-gacalc-matrix-template.md` (blocked on geometricalgebra `tasks/matrix-template-compile-once.md`). Go-ahead from William Emerison Six <billsix@gmail.com> 2026-09-06 ("I love it"), with one correction: the translation vector is written as gacalc's idiom, a **linear combination of the basis vectors** (`tx * g3.Vector.e_1 + ty * g3.Vector.e_2`), never `g3.Vector(tx, ty, 0)` (geometricalgebra's `CLAUDE.md`: every term carries its coefficient; a blade used as a direction stays bare). Fable executing.
**Priority:** 6
**Difficulty:** 4
**Depends on:** nothing; **relates to** the parked `tasks/pgzero-gl-step3-reextract-library.md` (an engine change today touches eleven files; after step 3 it would touch one).

## BLUF

Replace each game engine's hand-built `_translate(tx, ty) @ _scale(w, h)` (per sprite per frame) with a
matrix whose *definition* is gacalc — `to_matrix(translate(b=tx * g3.Vector.e_1 + ty * g3.Vector.e_2) @
scale_non_uniform(w, h, 1), g3.Vector, backend="sympy")` evaluated **once at import with sympy
symbols** — and a compiled per-draw fill that is 7× faster than today (0.47 µs vs 3.19 µs, measured).
Same for `ortho_pixels` (`translate(b=-1 * g3.Vector.e_1 + 1 * g3.Vector.e_2) @
scale_non_uniform(2/w, -2/h, -1)`, built once).
Byte-identical output is expected (the matrices are equal, `np.allclose` and structurally), so the
usual gates apply. Details and numbers: `tasks/reference/gacalc-transforms-in-the-renderer.md`.

## Plan

1. In one game (boing), add to the renderer section:
   ```python
   _TX, _TY, _W, _H = sympy.symbols("tx ty w h")
   MODEL = MatrixTemplate.compile(
       translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2) @ scale_non_uniform(_W, _H, 1),
       (_TX, _TY, _W, _H),
   )   # a frozen dataclass: the constant 4x4 + (row, col, parameter) slots; MODEL.fill(tx, ty, w, h)
   ```
   (the exact code is `tasks/adhoc/pgzero-gl-renderer-matrix-via-gacalc-perf/bench_model_matrix.py`,
   `gacalc_compiled`); use it in `draw_image`/`filled_rect`/`draw_image_region`; drop `_translate`/`_scale`.
2. Gates: `tools/ctc_verify_game.sh` frame identity, the state trace, ruff + ty, pytest.
3. Codemod the other ten engines (a `tasks/adhoc/` script, idempotent), gate each.
4. Reference doc §1b / the tightening reference: note the renderer's matrices now come from gacalc.

## Open question

1. Do you want this at all? It adds a sympy import and ~15 lines to every engine for "one source of
   truth"; the numeric gain is real but irrelevant at 60 Hz. *(Fable's read: yes if the point of the
   course's renderer is to show the maintainer's math end to end; otherwise leave it for step 3.)*

## Work record (2026-09-06, Fable)

- Pre-flight in the container: the linear-combination form `_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2`
  works over sympy symbols (gacalc's `__rmul__`); the compiled fill is `np.array_equal` to
  `_translate @ _scale` for 5000 random `(tx, ty, w, h)` plus the zero-width bar and integer cases;
  the gacalc-built `ortho_pixels` is `array_equal` to the hand-built one for every window size in use.
- `tasks/adhoc/renderer-model-matrix-from-gacalc/model_matrix_from_gacalc.py`: `ast`-locates the three
  helpers and asserts they are the shared text, replaces `_translate`/`_scale`/`ortho_pixels` with the
  comment block + `MatrixTemplate` (frozen slotted dataclass; `compile(fn, params)` classmethod, `fill`)
  + `MODEL` + the gacalc `ortho_pixels`, rewrites the one or three `_translate(...) @ _scale(...)` sites
  to `MODEL.fill(tx, ty, w, h)`, and merges `sympy`, `gacalc.g3`, `gacalc.transforms` and `Sequence`
  into the existing import lines. Idempotent (second run: ten "already converted"). `boing_gl1.py`
  untouched (fixed-function `glTranslatef`/`glScalef`).
- Gates: eleven frame gates AE=0 vs HEAD (which predates both the classmethod and this change, so the
  comparison spans both); the nine trace runners identical over 1500 frames; ruff + ty clean; 104 tests.
- One-shot codemod, held in `tasks/adhoc/` until the maintainer says "archive".
