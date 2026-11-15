# Code the Classics: inline pgzero_gl per game, strip + restructure, then re-extract (done 2026-11-15)

**Durable record:** `tasks/reference/code-the-classics-tightening.md` (the game shape, §9 the shared modules),
`tasks/reference/library-not-framework-authorship-style.md` (why), `tasks/reference/notable-subsystems.md` §4a.

## What it was

The 11 Code-the-Classics game files had been framework-style clients of the shared `pgzero_gl` PyGame Zero
shim: its `runner.main()` owned the loop and called back into each game's `update()`/`draw()`, the
inversion of control the course argues against. The initiative turned them into library-style programs in
three steps: inline the borrowed abstraction, restructure each copy, then re-extract only the seams that
turned out to be real. The risk named up front was that step 3 would never happen and leave 11 divergent
copies; the criterion for step 3 was set before extracting.

## Steps

1. **Inline the shim into each game** (2026-09-04): the whole shim copied to the top of each game file, the
   `pgzero_gl` imports removed; byte-identical frame-trace proof.
   `tasks/archive/2026/09/04/pgzero-gl-step1-inline-per-game.md`.
2. **Strip and restructure** (2026-09-04, play-tested good 2026-09-05): each copy cut to what its game uses,
   dataclasses, and each game took ownership of its loop.
   `tasks/archive/2026/09/05/pgzero-gl-step2-strip-and-restructure.md`. The tightening pass then reshaped all
   ten games to one standard: `tasks/archive/2026/09/05/codetheclassics-tighten-games.md`.
3. **Re-extract the shared library** (2026-11-15, after being parked 2026-09-06 to 2026-11-15): the audio mixer,
   image loading and GL helpers moved into `src/modelviewprojection/pgzero_gl/` (`audio`, `resources`, `gl`),
   which the games call down into; everything else stayed per game.
   `tasks/archive/2026/11/15/pgzero-gl-step3-reextract-library.md`.

Side branch: `boing_gl1.py`, the fixed-function OpenGL 1.x rendering of boing, readable as a `diff` against
`boing.py` (`tasks/archive/2026/09/05/pgzero-gl-boing-gl14.md`).

## Decisions (maintainer, William Emerison Six <billsix@gmail.com>)

- **2026-09-04:** step 1 copies the whole shim into each game file (one file per game, read top to bottom
  like the demos); step 2 absorbs the loop into each game; three step tasks under this umbrella.
- **2026-11-15:** step 3's criterion is at least 7 of 11 files in the same shape plus "teaches nothing about
  the game"; the library lives in the package's `pgzero_gl/` directory. Detail in the step-3 record.

## Verification method

Every step was behaviour-preserving, checked per game with a seeded frame capture (pixel identity) and a
seeded scripted-input state trace, both now in `tools/` (`ctc_verify_game.sh`, `ctc_state_trace.py`,
`ctc_compare_traces.py`, `ctc_gate_all.sh`). Audio and gamepad input are play-tested by hand.
