# Remove the now-misleading pygame / PyGame Zero comments from the Code-the-Classics code

**Status:** DONE + ARCHIVED 2026-09-05 (as subsumed — every game's comments concern was covered by the tightening pass; see the umbrella's completion record).
the comment strip runs as one of that umbrella's three per-game concerns. This doc stays as the
comment-concern checklist (the ~987-mention breakdown, the comments-only-never-identifiers rule) and
is archived as subsumed once every game's comments are done. Not an independent actionable task.
**Priority:** 4
**Difficulty:** 5
**Progress (2026-09-05):** boing + boing_gl1 DONE inside the tighten pilot (67 → 2 mentions; the 2
are the `PGZERO_MAX_FRAMES` harness env var). **Open Q1 decided by Fable:** the
`# ===== pgzero_gl/<mod>.py =====` banners are replaced NOW by plain `# ===== engine: <what> =====`
banners (not left for step 3). **Open Q2 as recommended:** accurate behaviour contracts are kept,
reworded as plain statements. Per-game comment census (game-part lines to judge, with the
keep-the-rationale ones marked) is in each `tasks/codetheclassics-tighten-<game>.md`.

## BLUF

Strip the comments and docstrings that describe the Code-the-Classics code as a
**pygame / PyGame Zero API reimplementation**, across the games (`ports/codetheclassics/`) and the
inlined shim (`src/modelviewprojection/pgzero_gl/`). After the inline → strip → make-specific work
(steps 1–2 of the umbrella), each game owns purpose-specific code that is **no longer a faithful
pygame-zero reimplementation**, so those comments now mislead. **This is accuracy, not concealment —
pygame's influence is real and stays acknowledged where it's true; the misleading "this IS pygame"
framing is what goes.** Scope: **~987 mentions** (844 in the games — inflated ~11× because the shim
is inlined into each game — and 143 in the shim). **Comments/docstrings only — never identifiers.**

## Context

- **Why (maintainer, 2026-09-05):** *"all of the comments in the code about pygame zero are to be
  removed. I'm not trying to hide its influence, it's just misleading now."*
- **Rides on:** the umbrella `tasks/pgzero-gl-inline-strip-reextract.md` — this is the comment-level
  companion to step 2 (make-specific per game); do it before or alongside step 3 (re-extract).
- **Overlaps the licensing pass — do NOT double-handle:** the file-header block
  (*"clean-room reimplementation of the pygame / PyGame Zero APIs … LGPL"*) is rewritten by
  `tasks/codetheclassics-licensing-after-shim-inline.md` (the approved **BSD-2-Clause** header pass).
  Coordinate: let the licensing pass own the headers; this task owns the *body* comments/docstrings.

## Scope and judgment calls (this is not a blind find-replace)

1. **Identifiers stay, always.** The module name `pgzero_gl`, `from modelviewprojection.pgzero_gl
   import …`, class/attribute names — removing these breaks the code. This task touches **comments
   and docstrings only.**
2. **Keep the rationale, drop the pygame framing.** Comments that explain a *value or behavior* via
   pygame (e.g. *"pygame.mixer defaults to 8 mixing channels; cap concurrent voices per Sound at
   8"*) carry real design rationale — rephrase to state the reason without the pygame attribution
   (the "why we cap at 8" survives), don't delete the information.
3. **The `# ===== pgzero_gl/<mod>.py =====` inlined-module banners** mark the inlined structure.
   Decide (Open Q1) whether they go now or survive until step 3 re-extraction reorganizes them.
4. **Headers are the licensing task's**, not this one (see Context).

## Verify

- `grep -rniE "pygame|pgzero" ports/codetheclassics src/modelviewprojection/pgzero_gl` returns only
  **identifiers** (imports, the module name) and any deliberately-kept, still-true attribution — no
  "this is a pygame reimplementation" body comments.
- Games still run byte-identical (the step-1/2 frame-trace harness, `tasks/adhoc/pgzero-gl-inline/`).
- `make format` clean on `ports` (ruff + ty).

## Open questions

1. **Inlined-module banners** (`# ===== pgzero_gl/audio.py =====`) — remove as part of this pass, or
   leave until step 3 re-extraction, which will reorganize the module boundaries anyway?
   *Recommend leaving them until step 3 (they still document where the inlined slices came from).*
2. **Shim compat-notes** — some shim docstrings describe pygame API *semantics* the shim faithfully
   matches (e.g. `Rect` is integer-coord *"like pygame.Rect"*). Strip these too, or keep as
   still-true compatibility notes? *Recommend keeping the few that are accurate behavior contracts,
   rephrased as plain statements of behavior.*
