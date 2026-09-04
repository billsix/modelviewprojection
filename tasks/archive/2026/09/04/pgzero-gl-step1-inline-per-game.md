# Step 1 — inline pgzero_gl into each Code-the-Classics game file

**Status:** DONE — all 10 games inlined & proven behavior-preserving 2026-09-04 (staged; maintainer commits)
**Priority:** 4
**Difficulty:** 4
**Part of:** `tasks/pgzero-gl-inline-strip-reextract.md` (umbrella) · **Next:** `tasks/pgzero-gl-step2-strip-and-restructure.md`

## Result (2026-09-04)

All **10** Code-the-Classics games are now single self-contained files (the shim pasted at the top, game code
below); ruff-clean; each proven behavior-preserving by a **byte-identical frame-180 trace** (AE=0 vs the
original, after a determinism sanity check comparing the original to itself). Final line counts: boing 3528,
cavern 4014, myriapod 4096, bunner 4118, soccer 4407, kinetix 4434, avenger 4766, eggzy 5037, leadingedge 5450,
beatstreets 6324.

The mechanism (all in `tasks/adhoc/pgzero-gl-inline/`, saved + reusable):
- **`inline_game.py`** — the codemod. Concatenates the 18 shim modules in dependency order, consolidates external
  imports (E402), self-aliases the shim's internal namespaces (`context`/`audio`/`_text`, plus a game's imported
  submodule namespaces like `joystick`/`gldraw`) to `sys.modules[__name__]`, turns aliased imports into plain
  assignments (`GLImage = Image`, emitted AFTER the shim so the target exists), neutralizes indented/deferred
  relative imports (e.g. `runner._select_renderer`'s `from .renderer import Renderer`) to `pass`, and renames
  game-vs-shim top-level collisions (`draw`) to `_pgz_draw` — scoped to module-level defs so `Actor.draw` is
  untouched.
- **`capture_frame.py`** — seeds RNG, monkeypatches `glfw.swap_buffers` to `glReadPixels` frame N deterministically.
- **`verify_step1.sh`** — inline → ruff → frame-identity trace, PASS/FAIL per game. **Reusable for step 2's
  behavior-preservation checks** (a step-2 restructure must keep the same frame-identity property).

Caveat on the proof's scope: the trace exercises the deterministic no-input path (no keyboard/gamepad, no audio
device). It is a *complete* proof for a pure code-move like this inline; step 2's restructure will want human
play-testing on top, since it changes structure (and absorbs the loop).

## BLUF

Copy the whole `pgzero_gl` shim to the **top of each of the 11 game `.py` files** and remove that game's
`from modelviewprojection.pgzero_gl import …` lines, so each game becomes a single self-contained file — engine
at the top, game below, read top-to-bottom — like a course demo. **Purely mechanical and behavior-preserving;**
no gameplay changes. The maintainer commits after this step (its natural handoff boundary). The stripping and
loop-absorption happen in step 2, not here.

## Context

- **Read first:** the umbrella `tasks/pgzero-gl-inline-strip-reextract.md` (vision, risks, the re-extraction
  goal) and `tasks/reference/library-not-framework-authorship-style.md` (why single-file top-to-bottom IS the
  house style). The shim being inlined is `src/modelviewprojection/pgzero_gl/` (18 files ≈ 3.4k lines after the
  2026-09-04 dead-code removal); its map is `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md`.
- **The 11 games:** `ports/codetheclassics/vol1/{boing,cavern,myriapod,bunner,soccer}` and
  `vol2/{kinetix,avenger,eggzy,leadingedge,beatstreets}`. (Note: repo docs say "10/11 games" in places — confirm
  the exact set from the directory tree at execution time.)

## The mechanism (per game)

1. **Concatenate the 18 `pgzero_gl` modules into the top of the game file, in dependency order.** Leaf modules
   first (`_types`, `geometry`), then the ones that build on them (`context`, `resources`, `renderer`,
   `renderer_gl1`, `surface`, `screen`, `draw`, `mask`, `transform`, `text`, `actor`, `input`, `joystick`,
   `audio`, `runner`), then the `__init__.py` module-level glue last. **The one real subtlety:** code that runs
   at import time — module-level singletons like `screen = Screen()`, `music = _Music()`, `keyboard = Keyboard()`
   — must appear AFTER the class it instantiates, or the file fails to load. Order by "definition before use at
   module load", not just by file.
2. **Drop the shim's intra-package imports** (`from . import context`, `from ._types import …`, `from .renderer
   import _rgba`, …) — everything is one namespace now.
3. **Consolidate the shim's external imports** (numpy, `OpenGL.GL`, glfw, PIL, gacalc, miniaudio, stdlib) into the
   game file's single import block; de-duplicate against the game's own imports.
4. **Remove the game's `from modelviewprojection.pgzero_gl import …` lines** — those names are defined above now.
5. Leave `src/modelviewprojection/pgzero_gl/` **untouched** (still the shared source of truth until step 3).

## Do it with a saved, re-runnable script

Write the concatenation as an ad-hoc script under `tasks/adhoc/pgzero-gl-inline/` (per the ad-hoc-scripts
convention) so the 11-game inline is reproducible and the ordering logic is a committed record, not an
un-reproducible hand-edit. Make it idempotent and prove it (run twice → second run is a no-op).

## Verification (per game, before handoff)

- **Loads + runs headless:** each game imports without error and runs under Xvfb with `PGZERO_MAX_FRAMES` + the
  pixel-mean check (the established recipe; see the step-tasks' shared verification in the umbrella and the
  2026-09-04 dead-code work record `tasks/archive/2026/09/04/pgzero-gl-remove-dead-code.md`).
- **Behavior-identical:** a seeded differential state trace (the technique from
  `tasks/archive/2026/07/23/frozen-vectors-rebind-migration.md`) shows no divergence vs. the pre-inline game —
  inlining moves code, it must not change a single frame.
- `ruff` + `ty` clean on each inlined file (they'll be large; that's expected and fine).

## Open questions

None blocking — the mechanism is decided. If a game's import-time ordering turns out genuinely circular (not just
"singleton after class"), stop and note it in the umbrella rather than forcing it.
