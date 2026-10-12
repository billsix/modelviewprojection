# Replace book figure generation with ePiX (ported from geometricalgebra)

**Status:** done 2026-10-12 (William Emerison Six <billsix@gmail.com>) — remaining
polish tracked in `tasks/review-epix-figure-migration.md`
**Priority:** 6
**Difficulty:** 7
**Created:** 2026-10-11 (William Emerison Six <billsix@gmail.com>)

## BLUF

The book's *mathematical coordinate/vector/transformation plots* are now generated
by **ePiX** (the C++ figure library + its Python front-end), built locally
in-container behind a `USE_EPIX` build flag — the pattern the sibling
`geometricalgebra` repo established. ePiX replaced the two math-plot toolchains:
the gnuplot plots and the `generate_plots.py` matplotlib frames. It **coexists**
with graphviz Cayley graphs, `texExpToPng`/`inlinetex`, and the executed notebooks,
which stayed (ePiX is the wrong tool for graph auto-layout, math-expression
rasterization, and notebooks — gacalc made the same coexist call). The authoritative
description of the resulting toolchain now lives in
`tasks/reference/book-figures-and-images.md`; this doc is the work record.

**35 live figures were ported** (1 `modelspace` + 21 transform frames + 13 gnuplot
statics) and parity-checked against the originals; the transform figures **drive
mvp's own taught code** (`modelviewprojection.mathutils` over gacalc `Vector` /
`InvertibleFunction`s), so each picture is produced by the exact functions its
chapter teaches. The ~18 orphaned `generate_plots.py` families (confirmed dead) and
the old generators were retired. The clean containerized book build (html +
latexpdf + epub) is green with no figure-related warnings.

## What was built

- **Container (`USE_EPIX` install).** `Dockerfile` gained `ARG USE_EPIX` / `ARG
  EPIX_COMMIT` as a self-contained LATE layer — declared right before use, scripts
  COPYed from `entrypoint/epix/` (not matched by the early `COPY entrypoint/*.sh`),
  and placed ABOVE the `COPY . /mvp` baked-source layer, so toggling the flag or
  bumping the commit rebuilds only this layer and never the expensive texlive/dnf
  layer. Two scripts: `entrypoint/epix/install-epix-deps.sh` (the render toolchain
  dnf) and `install-epix.sh` (shallow fetch of the pin → meson install → nanobind
  build via epix-mirror's own `build_py.sh` → the `/epix`→`/opt/epix-src` shadow-fix
  move → editable install). `Makefile` gained `USE_EPIX ?= 1` + the `--build-arg`.
  Verified in-image: `epix --version` → 1.2.22, `import epix` OK.
- **Renderer.** `tools/render_epix_figures.py` (ported from gacalc): runs each
  non-`_`-prefixed figure in a **fresh interpreter** (`runpy` in a subprocess —
  `libepix` keeps global drawing state with no reset), writes `<name>.pdf` via
  `elaps --pdf` and `<name>.png` flattened onto a solid background with ImageMagick
  (so dark-mode HTML pages don't show a transparent sheet). Output →
  `book/docs/_static/epix/`. Guard: exit 2 with a message when `elaps` is absent (a
  lean / `USE_EPIX=0` image), so the degrade is clean, not cryptic.
- **The 35 figures**, authored as jupytext percent `.py` under `book/figures/epix/`,
  one figure per file (the fresh-interpreter rule), every argument keyword-only:
  - **13 gnuplot statics** via `_scene2d.py`'s `framed_plot_scene` (variable
    range/aspect/tick-interval, bottom-left numbers, `set size ratio` via unequal
    `scale_x`/`scale_y`), with `clipped_rect` (Liang–Barsky — the screenspace
    paddles clip to the monitor) and `plot_path`/`plot_markers`/`plot_text`:
    `monitor`, `monitor2`, `screenspace`, `screenspace2`, `ndcSpace`, `ndcSpace1`,
    `viewport`, `plot1`–`plot4`, `disproportionate1/2`. Static diagrams — no
    transform, so no `mathutils`.
  - **21 transform frames + `modelspace`** via `_transform_sequence.py`'s
    `transform_frame`, which draws the modelspace frame as the transform applied to
    the basis (one rule covering translate, scale, and rotate) and places the paddle
    by the same transform — all from `mathutils` (`translate`/`rotate`/
    `scale_non_uniform`/`compose`) over gacalc types:
    `translation-forwards-{0,2,3}`, `translation2-forwards-{0,2,3}`,
    `scale-{0,2,4}`, `incorrectrotate-forwards-{1..6}` (rotate about the WRONG
    centre — the taught mistake), `rotate-sloppy-forwards-{3..8}`, and `modelspace`
    (the ch16 paddle). The rotation round-1 and scale frames turn/stretch the whole
    grid under one `frame_transform` with Liang–Barsky clipping, matching the
    originals (decision Q6 = full fidelity).
- **Rewire + retire.** `.rst` refs rewired (42 refs across ch01–04, 06–08) from
  `_static/<name>.svg` → `_static/epix/<name>.*` (wildcard → PDF for latex, PNG for
  html) by a one-shot idempotent codemod (`rewire_rst.py`, removed at archive —
  see git history). Retired (git rm): `src/modelviewprojection/plotsforbook/`
  (`generate_plots.py` + `plotutils/`) and `book/docs/_static/gnuplot/`; removed the
  `generate_plots_for_book` console script + `plotsforbook` per-file-ignore from
  `pyproject.toml`, the `plotsforbook` entry from `pytest.ini`, and the
  `rotate0-0.svg` dummy target + `cd gnuplot && make` from `_static/Makefile`.
  `util/nbplotutils.py` (notebook matplotlib helper) was KEPT — separate concern.
  `entrypoint.sh` now runs `python tools/render_epix_figures.py` before the Sphinx
  build (after the editable install, so `mathutils` is importable). `.gitignore`
  gained `book/docs/_static/epix/` and dropped the dead `_static/gnuplot/*` rules.
- **Left frame edge fix.** `epix.Path(closed=True)` does not stroke the implicit
  closing edge, so the ch2 / rotation frames were missing their left-hand line.
  Fixed in `_scene2d.py` by giving each box Path an explicit closing point (three
  sites: `framed_plot_scene` border, `_frame_with_ticks`, `filled_rect`).
- **gacalc 0.0.20 adaptation.** master runs gacalc 0.0.20, whose 2D vector type is
  `g2.Vector` (the `g2.Vector2` the figures first used on the `morePorts` branch, at
  gacalc 0.0.14, was renamed). `_transform_sequence.py` — the only figure file that
  drives gacalc — was updated to `from gacalc.g2 import Vector`; the rest of the API
  (`.x`/`.y`, `translate(b=)`, `rotate`, `scale_non_uniform`, `compose`, `.e_1`/
  `.e_2`) was unchanged. All 21 transform figures re-verified on 0.0.20.

## Verification

Clean tree (`git clean -fdx`) in a fresh container: the 35 ePiX figures rendered
(png + pdf); `_static/make` built the dot + tex figures; **`sphinx-build -M html`
(rc 0), `-M latexpdf` → a 289-page PDF using all 35 ePiX PDFs (rc 0), and `-M epub`
(rc 0, 15 MB)** all succeeded, zero figure-related warnings, every `_static/epix/*`
ref resolved (2026-10-12). Side-by-side parity PNGs were generated into
`output/epix-parity/` (gitignored) throughout the port.

Two incidental finds during verification, both unrelated to the figures:
- **Pre-existing shading doctest** — `util/shading.py::_face_normal` returned sympy
  `(Zero, Zero, Float)` instead of the floats its `-> tuple[float, float, float]`
  signature promises (gacalc routes integer-valued input through sympy). The real
  `make html` runs `pytest --exitfirst` before the docs, so this blocked the build.
  Coerced the return to `float`; suite went green. (On master this was already
  fixed independently, so the port kept master's version.) Untouched since
  2026-07-19 — the figure migration did not break it.
- **Interactive spellcheck in the build path** — `make html` had an `aspell check`
  prerequisite that needs a TTY (dies "Stdin not a terminal" headless). Replaced
  with a non-interactive `tools/spellcheck.sh`; detail and options in
  `tasks/non-interactive-spellcheck.md`. The broader template drift this exposed is
  tracked in `tasks/conform-makefile-dockerfile-to-standard-template.md`.
- **Debugging gotcha (recorded for next time):** the image's *baked* `/entrypoint.sh`
  is stale relative to the live copy that `make html` mounts (`-v
  ./entrypoint/entrypoint.sh`). Running the baked one directly skips the render step,
  and the latex build then fails on unresolved `_static/epix/*.*` wildcards. A fresh
  `make image` re-bakes it. This was a red herring, not a figure bug.

## Decisions settled (2026-10-11, William Emerison Six <billsix@gmail.com>)

- **Q1 — Scope = math plots only.** ePiX replaced the gnuplot and matplotlib
  figures; graphviz Cayley graphs, the `texExpToPng`/`.tex` labels, `inlinetex`, and
  the executed notebooks stayed. The `.tex` labels stay regardless of ePiX because
  the `.dot` graphs embed them as `<IMG SRC>`.
- **Q2 — Per-frame static; no animation.** There are **no generated animated GIFs**
  in the book (the only `.gif` is external CC-BY-SA art). The matplotlib
  "step-sequence" families were embedded as individual stills, so the ePiX figures
  are per-frame static; ePiX's `flix` animation path was dropped from scope.
- **Q3 — Drive mvp's own taught code.** The transform figures import
  `modelviewprojection.mathutils` and compose gacalc `InvertibleFunction`s — the
  picture is generated by the functions the chapter teaches. This retired
  `plotutils/mpltransformations.py`.
- **Q4 — Pin `EPIX_COMMIT = ebf3ca607ae6c1d4fa307e8b0359960d875d219c`.** mvp the
  project is a consumer; it pins its dependencies in its own Dockerfile. It already
  pins **gacalc** (`gacalc==X` + `ARG GACALC_VERSION`); this added **`ARG
  EPIX_COMMIT`** pinning which `epix-mirror` *commit* mvp builds against. That value
  is the same commit gacalc pins and `epix-mirror` master as of the port — all three
  in lockstep; bump together later.
- **Q5 — The ~18 orphaned `generate_plots.py` families were dead; dropped with the
  generator.** Confirmed by the maintainer (William Emerison Six <billsix@gmail.com>,
  2026-10-11): none was intended for an unwritten chapter. The `*-backwards`
  families plus `rotate0/1/2`, `covariance`, `circle`, `ortho2d`,
  `inverse-ortho2d` are referenced by no chapter, notebook, or assignment.
- **Q6 — Rotation round-1 frames replicate the rotated grid (full fidelity).**
  Implemented via one `frame_transform` driving grid + origin bands + axes with
  Liang–Barsky clipping, so a round-1 rotation turns the whole grid 65°/45° exactly
  like the original. Unifying this also corrected `scale-2` (its grid genuinely
  scales in the original).
- **Author in the Python front-end, not native `.xp`** (matches gacalc; figures
  stay runnable as jupytext notebooks); **reuse gacalc's install scripts, take the
  dnf package set from epix-mirror's current split scripts**; **separate output dir
  `_static/epix/`** (so ePiX and legacy outputs could coexist during the migration).

## Context (cold-start orientation)

- Resulting toolchain (authoritative): `tasks/reference/book-figures-and-images.md`.
- Sphinx build sequence + the `literalinclude` doc-region mechanism:
  `tasks/reference/book-and-docs-pipeline.md`.
- The gacalc precedent (sibling repo `/foo/opt/geometricalgebra`,
  `github.com/billsix/geometricalgebra`): its `book-and-docs-pipeline.md` §"ePiX
  figures", and the archived decision record `2026/10/07/epix-plot-integration.md`
  (pinned commit, `USE_EPIX` gating, the coexist-not-replace decision).
- ePiX source: `/foo/opt/epix-mirror` (`github.com/billsix/epix-mirror`, VERSION
  1.2.22, GPLv2+) — a C++20 library + bash driver scripts (`epix`/`elaps`/`laps`/
  `flix`) + an additive nanobind Python front-end. It produces LaTeX `picture`
  macros / eps / pdf / png; it is NOT a Python plotting library.

## Remaining

The review + finish pass the maintainer asked for is tracked in
`tasks/review-epix-figure-migration.md`: visual-parity sign-off, the marker-colour
and figure-source-E501 policy calls, the optional `check_epix_keywords` gate, and
confirming the `USE_EPIX=0` lean degrade.
