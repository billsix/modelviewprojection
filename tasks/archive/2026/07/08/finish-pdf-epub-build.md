# Task: confirm PDF + EPUB build is green after inlinetex migration

**Status:** COMPLETE 2026-07-08 — Bill's full build produced both artifacts
(`_build/latex/modelviewprojection.pdf` 8.6 MB, `_build/epub/
ModelViewProjection.epub` 15.8 MB, plus `output/`). Both failure modes this
doc predicted actually fired first and were fixed structurally the same day:
the "Unicode character" pdflatex death (a `√` U+221A via autodoc'd gacalc
docstrings, not a notebook glyph) is gone permanently via
`latex_engine = "lualatex"` (+ `latex_use_xindy = False`, five texlive
packages in the Dockerfile), and the stale-`.aux` "Runaway argument /
\@newl@bel" bit exactly as described (step 1's `rm -rf _build/latex` was the
cure). Remaining related item — inline-math "get the size reasonable"
(TODO.org, imgtex DPI knob) — stays open in TODO.org; it was never this
doc's core goal.

## Context
The `inlinetex` Sphinx extension + LaTeX→inlinetex migration (HANDOFF
2026-05-10) is committed, but **pdflatex was never confirmed green** after the
last fix. The PDF/EPUB currently in `book/docs/_build/` are stale (Mar 6,
pre-inlinetex), and `_static/inlinetex/` has 0 PNGs here (build not re-run in
this container). `texExpToPng` isn't installed in my container, so only Bill's
build exercises the rendering path.

## Steps (Bill runs; I diagnose failures)
1. `rm -rf book/docs/_build/latex` — clear any stale `.aux` that triggers a
   "Runaway argument? ... \@newl@bel" pdflatex error. (Auto-mode classifier
   blocks me from this rm.)
2. `make html` then `make latexpdf` then `make epub` in `book/docs/`
   (or just run `entrypoint/entrypoint.sh` via the container).
   - Expect ~60 `inlinetex*: generated …` lines (fresh PNGs at 150 DPI).
   - Watch for `! LaTeX Error: Unicode character …` — usually a progress-bar
     glyph (U+2588 `█`) leaking from a notebook. Reference fix:
     `src/modelviewprojection/notebooksrc/ndc.py:223` passes `logger=None` to
     moviepy's `write_videofile`. `framebuffer.py`/`plot2d.py` may need the same.
   - Send me the `l.NN` line on any Unicode death.
3. Confirm `book/docs/_build/latex/modelviewprojection.pdf` regenerates and the
   `.epub` builds.

## Related open item (TODO.org, 50%)
"Get the size reasonable" for inline math. Knob is
`inlinetex_default_size = 150` (`book/docs/conf.py:86`). If the 150-DPI PNGs
look pixelated/too-small in the PDF, bump to 200 and regenerate. TODO.org also
muses about making each equation independently sizable via the Makefile.

## Detailed spec
`tasks/archive/2026/05/10/sphinx-inline-tex-extension.md`, `tasks/archive/2026/05/10/sphinx-math-to-inlinetex.md`,
and `tasks/archive/2026/05/10/HANDOFF-2026-05-10.md`.
</content>
