# Code-the-Classics: the GL-resource factories become classmethods on their dataclasses

**Status:** DONE + ARCHIVED 2026-09-06 — codemod applied to all eleven files (34 factories moved: 3 per vol1 file, 3–4 per vol2), idempotent (second run: 0 changes); every frame gate AE=0 vs HEAD, all nine input traces identical (1500 frames each), ruff + ty clean, 104 tests; staged (the maintainer commits). Reference doc §1b records the rationale.
**Priority:** 3
**Difficulty:** 3
**Origin:** the maintainer's question (2026-09-05) "how do you flag to the programmer not to invoke the constructor directly but the factory?" — answered: Python has no private constructors; the standard signal is the classmethod alternative constructor (`dict.fromkeys`, `datetime.fromtimestamp`, `Path.home()`, `int.from_bytes`).

## BLUF

In all eleven game files, the free factory functions that build the GL-resource dataclasses move onto
their classes as `@classmethod`s, so the natural entry point is on the type and autocomplete shows it;
the dataclass constructors stay public (tests, or another backend such as `boing_gl1`, may pass their
own already-made GL objects) and each class docstring says "build one with `X.create(...)`".

| free function | becomes |
|---|---|
| `make_renderer(width, height)` | `Renderer.create(width, height)` (`Renderer1x.create` in boing_gl1) |
| `load_image(path)` | `Image.load(path)` |
| `image_from_rgba(arr)` | `Image.from_rgba(arr)` |
| `make_surface(width, height, transparent)` | `Surface.create(width, height, transparent)` |
| `mask_from_image(image, threshold)` | `Mask.from_image(image, threshold)` |

Not moved: `_link_program`/`_make_buffer` (private helpers of the renderer factory) and leadingedge's
`scale_image` (a transformation of an image, not a factory).

## Context

- The factory + dataclass shape itself was the maintainer's decision of 2026-09-05
  (`tasks/reference/code-the-classics-tightening.md` §1b, applied by the archived
  `tasks/adhoc/codetheclassics-tighten-games/renderer_dataclasses.py`). This task only changes
  *where the factory lives*, not what it does — no runtime value changes, so the gates are expected
  to pass byte-identically.
- Rejected ways to "hide" the constructor: `dataclass(init=False)` + a hand-written `__init__` (what
  the 2026-09-05 pass moved away from); a sentinel `InitVar` checked in `__post_init__` (enforcement
  theatre, breaks `dataclasses.replace`); underscore-prefixing the class (it is the annotation type
  everywhere).

## Plan / Verify

1. Codemod `tasks/adhoc/ctc-factory-classmethods/factory_classmethods.py` (ast-located moves, textual
   call-site renames; idempotent — a second run changes nothing) over the eleven files, then `ruff
   format`.
2. Gates per file: `tools/ctc_verify_game.sh <game> 180` (AE=0 vs HEAD), the state trace for the
   games with runners, `make format` (ruff + ty), pytest.
3. Reference doc §1b and the mvp `CLAUDE.md` line updated to the classmethod names.

## Work record (2026-09-06, Fable, overnight)

- `factory_classmethods.py` locates each factory with `ast`, lifts it under the class its return
  annotation names (`Renderer1x` in boing_gl1), rewrites `return <Class>(` to `return cls(` and a
  sibling factory call (`load_image` → `image_from_rgba`) to `cls.from_rgba(`, then renames the
  call sites (`_Loader("images", ..., Image.load)`, `Renderer.create(WIDTH, HEIGHT)`, ...) and the
  `:func:` cross-references to `:meth:`; the Renderer docstrings gain the "build one with
  `create`; the constructor takes already-linked GL objects" sentence. `ruff format` afterwards.
- Gates: `tools/ctc_verify_game.sh` frame 180 AE=0 for all eleven files; the nine games with trace
  runners (all but boing/boing_gl1, whose frame gate covers their whole attract mode) identical
  over 1500 scripted frames under `tools/ctc_compare_traces.py`; ruff and ty clean; 104 tests.
- One-shot codemod; it stays in `tasks/adhoc/ctc-factory-classmethods/` until the maintainer says
  "archive" (same holding rule as the tightening splices).
