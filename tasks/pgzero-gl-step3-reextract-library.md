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

## Open questions

1. **Set N** (the "shared in the same shape across ≥ N games" threshold) once the step-2 copies exist — defer
   until then. *(Recommendation: a clear majority, e.g. ≥ 7 of 11, for the first extraction pass; leave
   borderline things duplicated.)*
2. **Old shim's fate** (replace vs. keep-for-demos) — decide at extraction time with the copies in front of us.
