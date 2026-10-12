# Review the ePiX figure migration

**Status:** proposed — needs review
**Priority:** 3
**Difficulty:** 3
**Created:** 2026-10-11 (William Emerison Six <billsix@gmail.com>)

## BLUF

The book's gnuplot + matplotlib figures were replaced by ePiX
(`tasks/replace-book-figures-with-epix.md`, done 2026-10-11). This task is the
**review + finish** pass: eyeball the 35 ported figures against the originals,
decide the handful of open cosmetic/policy calls, and complete the doc/gate
loose ends before the maintainer relies on it. "Done" = every item below is
checked off (fixed, or consciously accepted). Nothing here blocks the book from
building — a clean containerized `sphinx-build html` already passes with zero
figure-related warnings; these are quality/polish/verification items.

## Context

- Work record + decisions: `tasks/replace-book-figures-with-epix.md` (Phases 1–5).
- The 35 figure sources: `book/figures/epix/*.py` (driven by
  `tools/render_epix_figures.py` → `book/docs/_static/epix/<name>.{pdf,png}`).
- **Side-by-side comparison images (generated during the port):**
  `output/epix-parity/` — `<name>-EPIX.png` next to `orig/<name>-ORIG.png`
  (gitignored; regenerate by rendering a figure and the corresponding original).
- Authoritative figure-toolchain doc to update: `tasks/reference/book-figures-and-images.md`.
- The migration kept graphviz (`.dot`), texExpToPng (`.tex` + `inlinetex`), and the
  executed notebooks (matplotlib via `util/nbplotutils.py`) — those are NOT ePiX's job
  and were deliberately left in place.

## Review checklist

### A. Visual parity (the main review — compare `output/epix-parity/`)
- [ ] **gnuplot family (13):** `monitor`, `monitor2`, `screenspace`, `screenspace2`,
  `ndcSpace`, `ndcSpace1`, `viewport`, `plot1`–`plot4`, `disproportionate1/2`. Check
  the gist: frame + ticks, paddle rectangles/paths, coordinate labels, the clipped
  "off-screen" paddles in `screenspace`, the stretched aspect in `disproportionate`.
- [ ] **transform family (21):** `translation-forwards-{0,2,3}`,
  `translation2-forwards-{0,2,3}`, `scale-{0,2,4}`, `incorrectrotate-forwards-{1..6}`,
  `rotate-sloppy-forwards-{3..8}`. Check the paddle positions per frame, the moving
  modelspace axes, and the **rotated grid** in the rotation round-1 frames
  (`incorrectrotate-4`, `rotate-sloppy-6`).
- [ ] `modelspace` (the ch16 paddle).
- [ ] Spot-check the figures **in the rendered PDF** (lualatex), not just the HTML
  PNGs — font size, line weight and label legibility at book scale can differ.

### B. Open cosmetic / policy calls
- [ ] **Marker colour.** The gnuplot coordinate plots' vertex dots render **black**;
  the gnuplot originals used **cyan** (`pt 7`). `plot_markers` has a `PLOT_MARKER`
  cyan default but ePiX `dot` draws in the pen colour — decide: keep black (cleaner),
  or make the markers actually cyan (needs a coloured-dot path in `_scene2d.py`).
- [ ] **`E501` in figure sources.** `book/figures/epix/*.py` and
  `tools/render_epix_figures.py` have comment/docstring lines > 80 cols. **`format.sh`
  does not lint `book/figures/` or `tools/`, so these are not gate failures.** Decide:
  reflow the comments/docstrings to 80 for house consistency, or leave (these sources
  are never displayed in the PDF — the 80-col rule targets displayed listings).
- [ ] **Tick intervals / aspect.** The gnuplot figures use hand-picked tick intervals
  and `scale_x`/`scale_y` approximating gnuplot's auto-choices and `set size ratio`.
  Confirm they read well; nudge intervals/scales if a figure looks off.

### C. Gate / tooling loose ends
- [ ] **Port `check_epix_keywords.py`** from gacalc (`/foo/opt/geometricalgebra/tools/`)
  and adapt its `KNOWN` table to mvp's helpers (`framed_plot_scene`, `coordinate_axes_scene`,
  `transform_frame`, `filled_rect`, `clipped_rect`, `plot_path/markers/text`, `point_label`,
  `vector`), then wire into `format.sh` — OR decide to skip it. (The figures already use
  keyword args throughout; this just enforces it.)
- [ ] **Full build:** run the real `make html` + `make latexpdf` + `make epub` in the
  container on a clean tree (`git clean -fdx` first) and confirm all three build. Only
  `sphinx-build html` was verified during the port.
- [ ] **`USE_EPIX=0` / lean degrade:** confirm a `BUILD_DOCS=1 USE_EPIX=0` image fails
  the renderer cleanly (the `elaps`-absent guard returns exit 2 with a message) rather
  than cryptically.

### D. Docs to update
- [x] **`tasks/reference/book-figures-and-images.md`** — DONE 2026-10-12 (pre-squash
  rewrite): §1 now describes four toolchains with ePiX in place of gnuplot + matplotlib,
  the clean-build note no longer cites the retired console script, and §4's imgconverter
  line is corrected.
- [x] **`CLAUDE.md`** — DONE 2026-10-12: item 4 added to the "Keeping the Dockerfile,
  Makefile … in sync" section (`USE_EPIX`/`EPIX_COMMIT` late layer, the `entrypoint/epix/`
  scripts, the pin matching gacalc, figures from `book/figures/epix/` driving `mathutils`).
- [ ] **`conf.py` imgconverter:** documented (keep it — it now serves only the remaining
  committed SVG art, `Maththing.svg` + CC images). Still confirm empirically in the full
  `make latexpdf` that nothing regressed when the math-plot SVGs disappeared.

### E. Cleanliness checks
- [ ] `rg "_static/(monitor|screenspace|ndcSpace|viewport|plot[1-4]|disproportionate|translation-forwards|translation2-forwards|scale-[024]|incorrectrotate|rotate-sloppy|modelspace)\.(svg|png)" book/docs/*.rst` → **zero** (all rewired to `_static/epix/<name>.*`).
- [ ] `rg "generate_plots_for_book|plotsforbook|_static/gnuplot" .` (excl. `.venv`, task docs/archive) → **zero live references** (retired).
- [ ] Clean-build warning count hasn't regressed vs the count recorded in
  `book-figures-and-images.md` (nbsphinx's 3 "kernel over TCP" warnings are expected
  and unrelated).

## Done-but-record

The migration itself: `USE_EPIX` container layer, the renderer, the 35 figures
(22 driving `mathutils`), the `.rst` rewiring (42 refs, codemod at
`tasks/adhoc/replace-book-figures-with-epix/rewire_rst.py`), and the retirement of
`plotsforbook/` + the gnuplot subtree. All staged; the maintainer commits.
