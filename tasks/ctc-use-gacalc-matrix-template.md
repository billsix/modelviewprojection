# Code the Classics: use gacalc's matrix template, delete the ten `MatrixTemplate` copies

**Status:** blocked
**Priority:** 8
**Difficulty:** 3
**Blocked on:** gacalc shipping the compile-once matrix template as a library feature —
`github.com/billsix/geometricalgebra` `tasks/matrix-template-compile-once.md` (proposed 2026-09-06 at
the maintainer's request: "eventually, not today").
**Recheck:** in the project container, `python -c "from gacalc.transforms import MatrixTemplate"` (or
whatever name that task settles on — read its Design §4) succeeds against the pinned gacalc; cleared
when it imports and the pin in `requirements.txt`/`Dockerfile` is a release that has it (`curl -s
https://pypi.org/pypi/gacalc/json | python3 -c 'import json,sys; print(json.load(sys.stdin)["info"]["version"])'`,
compared with a version-aware sort).

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
  MatrixTemplate.compile(translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2) @
  scale_non_uniform(_W, _H, 1), (_TX, _TY, _W, _H))` and the three/one `MODEL.fill(...)` call sites in
  `Renderer.draw_image` (+ `draw_image_region`, `filled_rect` where present).
- The archived task that put the copies there: `tasks/archive/2026/09/06/renderer-model-matrix-from-gacalc.md`.

## Plan (when unblocked)

1. Bump the gacalc pin (`requirements.txt` + the Dockerfile's `GACALC_VERSION`), `make image`.
2. A small idempotent codemod under `tasks/adhoc/ctc-use-gacalc-matrix-template/`: delete the
   `MatrixTemplate` class + its comment block from each engine, rewrite `MODEL = ...` to the library
   call, drop the now-unused `dataclass`/`Sequence`/`sympy` imports where nothing else uses them
   (ruff will say), keep `ortho_pixels`.
3. Gates per file: `tools/ctc_verify_game.sh` (AE=0), the state traces, ruff + ty, pytest.
4. Reference doc: note the copies are gone and gacalc owns the template.
