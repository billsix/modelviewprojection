# Step 3 — re-extract a library that actually makes sense

**Status:** PARKED — maintainer, 2026-09-06: "I don't want to re-extract yet"; stays its own task, not next-work until the maintainer says go. Steps 1 (inline) & 2 (strip/restructure) landed, and **the tightening pass that this step takes as input is complete (2026-09-05: all ten games, `tasks/archive/2026/09/05/codetheclassics-tighten-games.md`; the per-family engine flag list is `tasks/reference/code-the-classics-tightening.md` §6)**; it also inherits the licensing remainder — what becomes of the LGPL shim source under `src/modelviewprojection/pgzero_gl/` (`tasks/archive/2026/09/05/codetheclassics-licensing-after-shim-inline.md`). Steps 1–2 and **play-tested good (maintainer, 2026-09-05)**; this step is unblocked and actionable (the games are inlined/un-library-ized now — this step re-extracts the real shared library), awaiting the maintainer's call on the re-extraction criterion before extracting.
**Priority:** 9
**Difficulty:** 6
**Part of:** `tasks/pgzero-gl-inline-strip-reextract.md` (umbrella) · **Depends on:** `tasks/archive/2026/09/05/pgzero-gl-step2-strip-and-restructure.md`

## BLUF

With 11 stripped, restructured, loop-owning game files in hand, factor back out **only** what is genuinely
shared across them *in the same shape* — the real library the borrowed pgzero_gl framework was standing in for.
This is the payoff of the whole initiative; the risk the umbrella names is that this step never happens, leaving
11 divergent copies. What stays per-game duplicated is a feature (the house "teach once, then share is optional"
rule), not a failure.

## Context

- **Read first:** the umbrella `tasks/pgzero-gl-inline-strip-reextract.md` (holds the re-extraction criterion)
  and `tasks/reference/library-not-framework-authorship-style.md` (the extracted library must be *called by* the
  games, never a loop that calls them — do not re-introduce the inversion we just removed).
- Input is the 11 step-2 outputs. Only start once enough of them exist to see the real commonality (boing +
  a few others is enough to begin; you don't need all 11 before looking).

## The re-extraction criterion (decide before extracting, not after)

A thing earns a shared home **only if**: (a) **≥ N games use it in the same shape** after step 2 (N to be set
when we see the copies — likely a majority, not just 2), AND (b) **sharing it does not re-introduce the framework
inversion** — a shared *function/class the game calls down into* is fine; a shared *loop/runner that calls the
game's update/draw* is exactly the thing step 2 removed and must not come back. When unsure, leave it duplicated.

## Work

1. Diff the 11 step-2 files for genuinely-identical, same-shape units (renderer, resource loading, the input
   poll, the audio mixer — the audio mixer in particular is heavy and identical, a strong shared-library
   candidate; the loop is NOT — each game now owns its own).
2. Extract those into a small library the games import and **call down into**, per the criterion.
3. Decide the fate of the old `src/modelviewprojection/pgzero_gl/`: does the new extracted library replace it,
   or does it stay for the demos while the games use the new one? Resolve explicitly.
4. Re-run every game's headless + differential-trace check after extraction — extraction must be
   behavior-preserving too.

## Input from the tightening analysis (2026-09-05)

The inlined engines are byte-identical within three families (cavern ≡ myriapod; eggzy ≡
beatstreets ≡ leadingedge; kinetix/avenger/soccer/bunner the same text with different alias
lines) — `tasks/reference/code-the-classics-tightening.md` §3. The tightening pass
(`tasks/archive/2026/09/05/codetheclassics-tighten-games.md`) runs BEFORE this step and produces one tightened engine
per family, spliced into the siblings; those tightened copies are this step's input, and the
per-game exceptions (only leadingedge uses the mixer fades, only avenger builds `mixer.Sound`,
only bunner/soccer use `Sound.play(-1)`) are the first data for criterion (a).

## Feasibility assessment (2026-11-05)

Requested by William Emerison Six <billsix@gmail.com>: now that both Code the Classics volumes are ported, is
extracting a library feasible, and would it cut duplication? **Yes, partially.** These are static measurements,
made with an AST comparison of the engine half of each game file (everything above `# ===== game code`); no
game was run.

**Where things stand:**

- The 11 files under `ports/codetheclassics/vol{1,2}/` total 29,341 lines. Every game owns its loop (e.g.
  `boing.py`, `# ===== main loop =====`) and none imports `pgzero_gl`.
- The engine halves total 12,842 lines. Their top-level definitions total 9,418 lines but only 3,929 distinct
  lines, so **about 5,500 lines are verbatim copies** of a definition in another file.
- **Identical in all 11:** `Image`, `_Loader`, `_key_cb`, `shutdown_audio`. **Identical in 10** (all but
  `boing_gl1`): the GL helpers `_compile`, `_link_program`, `_make_buffer`, `GLBuffer`, `Uniforms`,
  `ortho_pixels`.
- **Subset variants, where the largest copy is the union:** `_Engine` (4 variants), `Sound` (4), `_Music` (5),
  `_Voice` (4), `Actor` (4 variants, in 9 games, ≤32 lines differ), `Rect`, `Keyboard`, `blit`.
- **Divergent:** `Renderer` (8 variants, 87–203 lines) and `SpriteRenderer` (9 variants; copied per file on
  purpose, `tasks/reference/code-the-classics-tightening.md` §1 item 6).

| Group | Lines saved by sharing | Library size |
|---|---|---|
| Audio (`_Voice`, `_Engine`, `Sound`, `_Music`, `shutdown_audio`) | ~2,770 | ~340 |
| Assets (`Image`, `_Loader`, `_decode`) | ~1,030 | ~100 |
| GL helpers (the six above) | ~660 | ~75 |
| `Actor` / `Rect` / keyboard | ~1,690 | ~235 |
| `Renderer` / `SpriteRenderer` | ~1,280 | ~255 |

**Library, not framework: easy here.** The games already own their loops, so nothing would call back into a
game. A sketch of the API: `Sound.load(path)`, `sound.play(loops=0, volume=1.0)`, `music.play(name)` /
`music.fadeout(ms)`, `shutdown_audio()`, `load_image(root, name) -> Image` (CPU decode, lazy GL upload),
`compile_program(vs, fs)`, `make_buffer(...)`, `ortho_pixels(w, h)`.

**Risks:**

- It gives up part of "read one game file top to bottom", the step-1 choice recorded in the umbrella.
- A shared mixer carries leadingedge/avenger's fade and loop paths that boing dropped.
- **Licence:** the games are BSD-2 (`ports/codetheclassics/LICENSE`); the mvp package is GPL-2+. So the library
  must live under `ports/codetheclassics/` with a BSD-2 header, **not** under `src/modelviewprojection/`.
- Audio is never covered by `tools/ctc_verify_game.sh` / `ctc_state_trace.py`, so audio changes need a
  play-test.
- **Book:** no `doc-region` markers in `ports/`, and no `.rst` mentions these games.

**Two things that predate this assessment:**

- `src/modelviewprojection/pgzero_gl/` (18 files, 3,262 lines, LGPL-2.1) is dead. No code imports it. Its
  only references are `tests/test_ctc_actor_field_collisions.py` (which AST-reads `pgzero_gl/actor.py`), a
  comment in `tools/ctc_capture_frame.py`, `entrypoint/format.sh`, and ruff ignores in `pyproject.toml`.
- `ports/codetheclassics/README.md` is stale. It says the games import the shared shim, and that upstream has
  no licence file.

## Recommendation (2026-11-05)

Extract partially, in three steps:

1. **Clean up first.** Delete `src/modelviewprojection/pgzero_gl/`, point the actor-field test at a game file,
   clean the `format.sh` / `pyproject.toml` / `ctc_capture_frame.py` references, and fix the README. This
   answers open question 2.
2. **Extract only the code that teaches nothing and is the same shape everywhere:** audio, asset loading, GL
   helpers. Put them in one called-down module, e.g. `ports/codetheclassics/ctc_engine.py` (BSD-2). That is
   about 520 library lines replacing about 4,450 duplicated lines (~15% of the tree). Convert one game at a
   time; after each, run the pixel-identity gate (`tools/ctc_verify_game.sh`) and the trace gates
   (`ctc_state_trace.py`, `ctc_compare_traces.py`), then play-test the audio.
3. **Keep per game:** the loop, `Actor`, `Rect`, `Keyboard`, `Renderer`, `SpriteRenderer`. They form the
   teaching gradient from boing (rawest) to beatstreets (richest). An N=7 threshold would admit `Actor` /
   `Rect` / `Renderer`; they are excluded on teaching grounds, not by count.

`cayley_gl` should **not** share this library: different stack (imgui + matrix stack vs. a 2D sprite renderer
+ mixer), different licence, and `ports/` stays independent of the package. Its own library-ification (done 2026-11-12) is
`tasks/archive/2026/11/12/cayley-gl-caller-owned-loop.md`.

## Open questions

1. **Set N.** Recommendation: ≥ 7 of 11 as the count test, plus the teaching exclusion above. Extract only
   audio, assets and GL helpers.
2. **Old shim's fate.** Recommendation: delete `src/modelviewprojection/pgzero_gl/`. Nothing imports it, and
   the games replaced it.
3. **Un-park this task?** It has been parked since 2026-09-06. Recommendation: un-park only step 1 (the dead-code
   cleanup) now, as a quick win; the extraction itself can stay parked.
