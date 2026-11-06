# Modernize the notebook's movie generation and upgrade moviepy

**Status:** proposed — needs go-ahead
**Priority:** 6
**Difficulty:** 4

## BLUF
The NDC notebook (`src/modelviewprojection/notebooksrc/ndc.py`) builds an
animation with `moviepy.ImageSequenceClip(...).write_videofile(..., codec="libx264")`.
To keep the Fedora 45 upgrade from changing calling code, we pinned
`moviepy==2.1.2` and **override moviepy's `pillow<12` cap** in the Dockerfile so it
coexists with `Pillow==13.0.0` (the only pillow with a cp315 wheel on Python 3.15).
That works but carries a dependency-override we'd rather not maintain. This task:
revisit *how* the notebook makes movies, upgrade to the newest libraries, and
update the calling code if a cleaner path removes the override. The maintainer is
fine changing historical calling code going forward, as long as it still works.

## Context
- The current working state + the full root-cause chain (unpinned moviepy
  backtracked to 1.0.3 under the Pillow-13/py3.15 conflict) is in the archived F45
  work and `tasks/reference/design-decisions.md`.
- Why the override exists: moviepy 2.x declares `pillow<12.0`; Python 3.15 only has
  cp315 pillow wheels at **12.3.0 and 13.0.0** (verified), so pillow must be ≥12.3
  on 3.15, always violating moviepy's cap. moviepy 2.x works with pillow 13 anyway
  (verified: `ImageSequenceClip` + `write_videofile(libx264)`), so the cap is
  conservative — hence the override rather than a downgrade.
- The usage is small: assemble a list of numpy RGB frames into a video, write an
  mp4 (libx264), embed via `IPython.display.Video`.

## Options to evaluate
1. **Drop moviepy; use `imageio` / `imageio-ffmpeg` directly.** imageio is already a
   dependency (`ImageIO` in requirements) and is moviepy's own backend, with **no
   pillow cap** — so this removes the override entirely. `imageio.mimwrite("x.mp4",
   frames, fps=60, codec="libx264")` (via imageio-ffmpeg) is close to a drop-in.
   Likely the cleanest end state. Verify the mp4 embeds identically in the book
   HTML/PDF pipeline (pdflatex capture — mind the progress-bar/U+2588 issue the
   current `logger=None` avoids).
2. **Keep moviepy, upgrade to the newest (2.2.1+) and retire the override if/when
   upstream raises the pillow cap.** Recheck moviepy's `pillow<…` constraint on each
   bump (`tasks/reference/design-decisions.md` notes the current cap); drop the
   Dockerfile override the moment a release allows pillow 13.
3. **Status quo** (pinned 2.1.2 + override) — fallback if 1 and 2 don't pan out.

Recommendation: try option 1 (imageio-direct) first — it removes the override and
drops a dependency; fall back to option 2.

## Done =
The NDC animation still renders (book HTML embeds the mp4, PDF builds), on the
newest viable libraries, with the Dockerfile pillow-cap override removed if option
1 or 2 allows. Update `requirements.txt`, the Dockerfile install, `ndc.py`, and the
design-decisions note together (the "three places must agree" rule in CLAUDE.md).

## Open question
1. Keep the output an **mp4/libx264** (current), or is a gif/webm acceptable? Affects
   which imageio backend/codec and the book embed. Recommend staying mp4/libx264.
