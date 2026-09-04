# Step 3 — re-extract a library that actually makes sense

**Status:** proposed — depends on step 2 (do not start until step 2 has landed for enough games)
**Priority:** 7
**Difficulty:** 6
**Part of:** `tasks/pgzero-gl-inline-strip-reextract.md` (umbrella) · **Depends on:** `tasks/pgzero-gl-step2-strip-and-restructure.md`

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

## Open questions

1. **Set N** (the "shared in the same shape across ≥ N games" threshold) once the step-2 copies exist — defer
   until then. *(Recommendation: a clear majority, e.g. ≥ 7 of 11, for the first extraction pass; leave
   borderline things duplicated.)*
2. **Old shim's fate** (replace vs. keep-for-demos) — decide at extraction time with the copies in front of us.
