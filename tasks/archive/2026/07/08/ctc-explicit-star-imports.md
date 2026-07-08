# Code the Classics: replace `from pgzero_gl import *` with named imports

**Status:** COMPLETE 2026-07-08 — every game's `from pgzero_gl import *`
replaced with a named import of its used subset (8-11 of the 12 names;
`exit` turned out to be called by NO game, so nobody imports it); bunner's
`from random import *` also made explicit (choice/randint/random).
F403/F405 removed from the ports ruff ignores — and the unmasking
immediately paid for itself: it caught a REAL latent bug (soccer's
honest-imports conversion used `gldraw.` in its debug-draw paths without
the import — a NameError waiting on DEBUG_SHOW_*) plus four upstream
loop-carried variables in leadingedge (used before their bottom-of-loop
assignment; noqa'd with explanation, faithful port). Gates: ruff fully
clean with the trimmed ignore list, all compile, ty clean both volumes,
in-container format.sh exit 0.
**Created:** 2026-07-08

## Goal (Bill, 2026-07-08)

Each game's `from pgzero_gl import *` becomes an explicit import of the
names it actually uses — the natural completion of the 2026-07-08
honest-imports work (tasks/ctc-honest-imports.md), which already made the
deeper pygame APIs explicit and shrank the star surface to the shim's
`__all__` of 12 names: `Actor, Rect, ZRect, keyboard, keys, images, sounds,
music, screen, go, exit, mixer`.

## How

- Per game, the used subset is easy to compute: for each of the 12 names,
  `grep -c '\b<name>\b'` the game (minus its own defs — only `exit` and
  `go` risk ambiguity; every game defines `draw`/`update` but those aren't
  exported). Typical result: `from pgzero_gl import Actor, Rect, keyboard,
  keys, mixer, music, screen, sounds, go` (one line, sorted).
- Keep the `# noqa: E402` (the import still follows the `sys.path.insert`
  dance — until/unless tasks/ctc-imports-at-top.md restructures that);
  drop the `F401,F403` parts and the name-list comment (the import line now
  IS the list).
- **Then remove `F403`/`F405` from pyproject's `ports/**` per-file-ignores**
  — with no star imports left, those suppressions are dead, and F405 was the
  single largest suppressed category (445 findings). ty also gets stronger:
  star-imported names were `Any`-ish; explicit ones resolve fully — expect
  (and want) a few new, real diagnostics; triage them like the
  honest-imports batch (widen shim signatures where the shim is wrong,
  faithful-port `ty: ignore` where upstream relies on runtime invariants).
- `exit`: the shim exports pgzero's game-quitting `exit()`. Games that call
  bare `exit()` currently get the SHIM's via the star import; an explicit
  import must include it or the builtin silently takes over — this is the
  one behavioural trap in the task. Grep each game for `exit(` and import
  accordingly.

## Gates

Per game: py_compile, ruff (with the trimmed ignore list), ty vs baseline,
boot on display. `_smoketest.py` and the shim README/examples also mention
the star-import idiom — update them to the named form.
