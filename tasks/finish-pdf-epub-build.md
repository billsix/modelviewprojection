# Task: confirm PDF + EPUB build is green after inlinetex migration

**Status:** blocked-on-Bill (needs the podman build container + a display-free
`make html`). The inlinetex code itself is committed (`e682de3`).

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
