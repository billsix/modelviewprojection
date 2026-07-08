# Code the Classics: hoist mid-function imports to the top of the file

**Status:** proposed — needs go-ahead
**Created:** 2026-07-08

## Goal (Bill, 2026-07-08)

All imports at the top of the file instead of inside functions.

## Scope + survey notes

Two kinds of function-local imports exist in the CTC tree; they need
different treatment:

1. **Shim lazy imports** (`pgzero_gl/`): `from . import context` inside the
   draw functions (`draw.py` — including the 2026-07-08 ones, which copied
   the pattern from `_make_pygame`), `resources`/`PIL`/`numpy` inside
   `transform.py`'s functions, `import sys` inside helpers, and similar
   spots in `runner.py`/`screen.py` etc. Most exist to avoid import cycles
   or to defer GL/PIL loading. **Audit each**: hoist where no cycle actually
   exists (likely most of them — e.g. `context` is probably cycle-free from
   `draw.py`); document the ones that must stay (a genuine cycle or a
   deliberate defer) with a one-line comment.
2. **Game-side local imports** (vol1/vol2): a handful of upstream
   `import X` inside functions. Hoisting is behaviour-safe except where the
   import has side effects timed to first call — none known, but verify per
   site.

Out of scope: mvp's own `src/` — note that `mathdemos`/`mvpvisualization`
deliberately import GL/PIL *inside* `main()` so the modules stay importable
headless (documented in `mathdemos/crossproduct.py`'s header); that design
is intentional and survives this task. This task is the CTC tree only,
unless Bill widens it.

## How

- `grep -rn "^\s\+\(import\|from\) " ports/codetheclassics --include="*.py"`
  is the worklist (indented import statements).
- Per file: hoist, run the cycle check (`python -c "import pgzero_gl"`,
  boot a game), `format.sh` gates (ruff/ty baselines unchanged).

## Gates

py_compile + ruff + ty (exact baselines) per chunk; a game boot on display
for anything where a hoist changes import timing (GL context creation must
still happen before GL calls — hoisting must never *execute* GL work at
import time, only bind names).
