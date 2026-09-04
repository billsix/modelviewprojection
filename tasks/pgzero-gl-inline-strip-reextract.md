# Code the Classics: inline pgzero_gl per-game, strip + restructure, then re-extract

**Status:** proposed — plan agreed, 2 design decisions open before the step-tasks are scaffolded (maintainer, 2026-09-04)
**Priority:** 4
**Difficulty:** 7

## BLUF

Turn the 11 Code-the-Classics games from **framework-style** clients of the shared `pgzero_gl` shim into
**library-style** programs that own their own code — by a three-step refactor: (1) copy `pgzero_gl` into each
game as a private copy, (2) per game, delete the dead slice and restructure the copy as that game needs
(dataclasses preferred), (3) re-extract whatever shared library actually makes sense from the 11 restructured
copies. This is the deliberate "inline the borrowed abstraction, then rediscover the real seams" move; it fits
the course's library-not-framework, duplication-is-fine philosophy. **The value is in step 3; the risk is step 3
never happening** (leaving 11 divergent ~3.4k-line copies), so the re-extraction criterion is named up front.

## Context (why this, and what's already true)

- **The motivation, verified 2026-09-04** by reading the actual demos + `pgzero_gl` (two subagent passes,
  `file:line`-anchored):
  - The course's **teaching demos** (`src/modelviewprojection/demos/`, demo01–24) are **library-style**: each
    owns its own module-level `while not glfw.window_should_close(window):` loop and calls *down* into
    `mathutils`/`matrix_stack`/`util`/glfw. Nothing calls the demo. (`wxapp.py` is the repo's framework foil —
    `app.MainLoop()` + `OnPaint`/`OnTimer`, the Qt/Hollywood inversion.)
  - The **Code-the-Classics games** (`ports/codetheclassics/{vol1,vol2}/`) are **framework-style**:
    `pgzero_gl.runner.main()` owns the loop and calls *back* into each game's `update()`/`draw()`/`on_*`. That
    is the same inversion of control the course argues against — the real reason to restructure them.
  - Both maintainer claims that motivate this — "library not framework" and "lots of repetition, increasingly
    adding complexity" — were assessed **accurate** with strong evidence. (Minor doc-drift found in passing, to
    fix separately: `CLAUDE.md` says "demo12: Matrix-stack concept introduced", but `fn_stack`/`FunctionStack`
    first appears in demo16–18.)
- **`pgzero_gl` today** is one shared package (`src/modelviewprojection/pgzero_gl/`, 18 files ≈ 3.4k lines after
  the 2026-09-04 dead-code removal) imported by all 11 games as `from modelviewprojection.pgzero_gl import …`.
  Its design, the **per-game usage slices** (which game uses joystick/surface/mask/transform, which parts are
  load-bearing vs fidelity), and the value-vs-behavior split are documented in
  `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md` — **read that first**; it is the map for
  steps 1–2 (it already says, per game, what is dead and what is used).
- **Fidelity rule still governs the games** (`CLAUDE.md` › Code-the-Classics): behavior-faithful ports —
  **no behavior changes** (same RNG call order, same update/draw order, same gameplay) — but *structure* may be
  modernized (dataclasses, `match`, annotations). The restructure in step 2 must stay behavior-preserving; the
  proven safety net is a **seeded differential state trace** (used for the frozen-vector migration —
  `tasks/archive/2026/07/23/frozen-vectors-rebind-migration.md`).

## Steps (this umbrella is the index; each step is its own task)

1. ~~inline the shim into each game file~~ → **DONE 2026-09-04** (all 10 games, byte-identical frame-trace proof;
   archived `tasks/archive/2026/09/04/pgzero-gl-step1-inline-per-game.md`). Staged; maintainer commits.
2. ~~strip dead slice, restructure, absorb the loop~~ → **DONE 2026-09-04** (all 10 games, byte-identical;
   the abstraction gradient realized — boing rawest at 1851 lines, beatstreets richest at 6014). Staged; maintainer commits + play-tests.
3. **`tasks/pgzero-gl-step3-reextract-library.md`** — re-extract the real shared library. *Step 2 done → unblocked; awaiting maintainer decision.*

**Side branch (not a step):** `tasks/pgzero-gl-boing-gl14.md` — a GL 1.4 fixed-function companion `boing_gl1.py`
beside the 3.3 `boing.py`, for studying the pipeline difference. Independent of step 3; awaiting go-ahead.

> **Adhoc cleanup at final archive (marked 2026-09-05):** when this initiative wraps and its `tasks/adhoc/pgzero-gl-*`
> scripts are triaged, **`git rm tasks/adhoc/pgzero-gl-boing-gl14/make_boing_gl1.py`** — it is a one-shot generator
> (its task archived 2026-09-05); kept for now only to avoid disturbing the adhoc tree while step 3 still needs the
> sibling `pgzero-gl-inline/capture_frame.py` harness. (Maintainer: leave it for now, delete at that archive.)

Ordering is expressed by priority + a "Depends on" note, NOT by `blocked` (that status is reserved for
*external* gates; a step waiting on an earlier step is within our control — just do them in order).

## The three steps

### Step 1 — inline pgzero_gl into each game file (mechanical; maintainer commits after)
**Decision (maintainer, 2026-09-04): option (b) — copy the whole shim to the TOP of each game's `.py` and remove
the game's `pgzero_gl` imports.** Each game becomes a single self-contained file — engine at the top, game below,
read top-to-bottom — exactly like the course's demos. Mechanically, per game:
- Concatenate the 18 `pgzero_gl` modules into the top of the game file, in dependency order (leaf modules like
  `_types`/`geometry` first; module-level singletons like `screen = Screen()`, `music = _Music()`, `keyboard`
  after their class defs). This ordering is the one real subtlety — the pieces that run code at import time must
  follow their definitions.
- **Drop the shim's intra-package imports** (`from . import context`, `from ._types import …`, etc.) — everything
  now lives in one namespace — and **consolidate the shim's external imports** (numpy, OpenGL, glfw, PIL, gacalc,
  miniaudio) into the game file's import block.
- **Remove the game's `from modelviewprojection.pgzero_gl import …` lines** — those names are now defined above.
- No behavior change. Verify every game still runs headless (Xvfb + `PGZERO_MAX_FRAMES` + pixel-mean check) and
  its seeded state trace is unchanged before handing off.
- The shared `src/modelviewprojection/pgzero_gl/` stays untouched until step 3 decides its fate.
- **Save the concatenation as an ad-hoc script** (`tasks/adhoc/…`) so the 11-game inline is reproducible and the
  ordering logic is a committed record, not a hand-edit nobody can re-run.

### Step 2 — per game: strip the dead slice, then restructure (dataclasses preferred)
For each game, using the per-game usage slice in the reference doc:
- **Delete what THIS game never touches** (e.g. vol1 games carry no joystick; only some use `surface`/`mask`/
  `transform`). Each copy shrinks a lot and becomes readable as "this game's engine."
- **Restructure the copy as the game needs** — dataclasses where they fit, and (see **Open decision #2**)
  optionally flip the framework→library inversion so the *game* owns its loop and calls down into its now-private
  renderer, instead of handing control to `runner.main()`.
- **Behavior-preserving**, verified per game by the seeded differential state trace + a headless render check.
- This is 11 games; expect it to span sessions. Track per-game status in the step-2 task.

### Step 3 — re-extract a library that actually makes sense
With 11 restructured copies in hand, factor back out only what is *genuinely* shared and stable across them.
**Re-extraction criterion (decide before extracting, not after):** a thing earns a shared home only if (a) ≥N
games use it **in the same shape** after step 2, and (b) sharing it does not re-introduce the framework
inversion (a shared *function the game calls* is fine; a shared *loop that calls the game* is the thing we just
removed). What stays per-game duplicated is a feature, not a failure — the same "teach once, then share is
optional" rule the demos follow.

## Risks (name them, don't discover them)

- **Step 3 stalls** → 11 divergent ~3.4k-line copies to maintain. Mitigation: treat step 3 as the point of the
  whole effort; don't consider the initiative "done" at step 2. If step 3 keeps slipping, that is a signal the
  re-extraction criterion needs to be stricter, not that the copies should stay forever.
- **Behavior drift across 11 games** — 11× the surface for a subtle RNG/update-order regression. Mitigation: the
  seeded differential state trace per game is mandatory, not optional.
- **Interim maintenance** — while steps 1–2 are in flight, a real shim bug fix must be applied to N copies.
  Mitigation: keep the shared shim as the source of truth until step 3; do step 2 game-by-game, not all-at-once.

## Open questions (must be resolved before the step-tasks are scaffolded)

1. ~~**Step-1 mechanism**~~ → **RESOLVED (maintainer, 2026-09-04): option (b)** — copy the whole shim to the top
   of each game `.py` and remove the game's `pgzero_gl` imports, making each game a single self-contained file
   like the demos. See Step 1 above for the mechanics.
2. ~~**Framework→library flip in step 2**~~ → **RESOLVED (maintainer, 2026-09-04): absorb the loop.** Each game
   owns `while not should_close: update(); draw()`; the inlined `runner.main()` loop is dissolved into the game.
   Captured in the step-2 task.
3. ~~**How many task files**~~ → **RESOLVED (maintainer, 2026-09-04): three step-tasks**, all children of this
   umbrella (see Steps above).

All decisions are made; the three step-tasks are scaffolded and ready to execute in order.

## Related

- `tasks/reference/pgzero-gl-design-for-a-personal-learning-library.md` — the per-game usage slices + what's
  load-bearing (the map for steps 1–2).
- `tasks/archive/2026/09/04/pgzero-gl-remove-dead-code.md` — the shared-shim dead-code removal (already done; the
  copies inherit the trimmed shim).
- `tasks/archive/2026/07/23/frozen-vectors-rebind-migration.md` — the seeded differential-state-trace technique
  for behavior-preserving game refactors.
